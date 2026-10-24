# Despliegue del POS

Arquitectura de despliegue (validada con el arquitecto):

- **Backend**: FastAPI en AWS Lambda (vía Mangum) + API Gateway HTTP API +
  DynamoDB (tabla única), desplegado con **AWS SAM**.
- **Frontend**: React + Vite servido por **AWS Amplify Hosting** (CI/CD desde el
  repo).

> Este repo deja el despliegue **preparado y validado**. Para ejecutarlo hacen
> falta credenciales AWS y las CLIs correspondientes; sin ellas, los pasos de
> publicación no se pueden correr aquí, pero sí están listos para un entorno con
> acceso.

## Estado de preparación

| Artefacto | Estado |
|-----------|--------|
| `backend/template.yaml` (SAM) | ✅ validado con `cfn-lint` (sin errores) |
| `backend/scripts/deploy.sh` | ✅ sintaxis verificada; idempotente |
| `backend/requirements.txt` | ✅ instala e importa limpio (deps de producción) |
| `frontend/amplify.yml` | ✅ build settings de Vite |
| `frontend` build | ✅ `npm run build` produce `dist/` sin errores |

## Requisitos (no incluidos en el repo)

- **AWS CLI** configurada con credenciales válidas (`aws configure`, SSO o rol).
- **AWS SAM CLI** para el backend.
- Una cuenta con permisos para crear Lambda, API Gateway, DynamoDB, IAM y SSM.

> **Nota sobre este entorno (sandbox del taller):** el contenedor corre bajo un
> rol de ejecución de Lambda (`MicroVMExecutionRole`) que **no tiene permisos de
> despliegue** (CloudFormation, DynamoDB, IAM devuelven `AccessDenied`), y la SAM
> CLI **no está instalada**. Por eso el despliegue no se puede ejecutar desde el
> sandbox: hay que correrlo desde un entorno con la SAM CLI y credenciales con
> permisos adecuados. Todos los artefactos ya están validados para ese momento.

## 1. Backend (AWS SAM)

```bash
cd backend
./scripts/deploy.sh pos-mvp us-east-1
```

El script:
1. Verifica que haya SAM CLI y credenciales (falla claro si faltan).
2. Crea el secreto JWT en SSM Parameter Store (SecureString) si no existe.
3. `sam build` y `sam deploy`.
4. Imprime la `ApiUrl` del stack.

> **Arquitectura/binarios**: `bcrypt` trae binarios nativos. Para garantizar
> compatibilidad con el runtime de Lambda, usa `sam build --use-container`
> (requiere Docker). El script usa `sam build` simple; añade `--use-container`
> si el entorno de build no coincide con la arquitectura de la función.

### Sembrar usuarios tras desplegar

```bash
cd backend
. .venv/bin/activate
AWS_REGION=us-east-1 POS_TABLE_NAME=pos \
POS_SEED_CASHIER_USER=ana POS_SEED_CASHIER_PASS='...' \
POS_SEED_OWNER_USER=don  POS_SEED_OWNER_PASS='...' \
python scripts/seed_users.py
```

(Las contraseñas se pasan por entorno; nunca se escriben en el repo.)

## 2. Frontend (AWS Amplify Hosting)

1. En la consola de Amplify, **conecta el repositorio** (rama principal).
2. Amplify detecta `frontend/amplify.yml` (build command `npm run build`,
   artefactos en `frontend/dist`).
3. Configura la **variable de entorno** en Amplify:
   - `VITE_API_URL` = la `ApiUrl` que imprimió el despliegue del backend.
4. Cada push a la rama dispara build + deploy automáticos.

> Dominio: usa el de Amplify al inicio; dominio propio después.

## 3. Verificación post-despliegue

```bash
# Salud del backend
curl https://<api-id>.execute-api.<region>.amazonaws.com/health
# -> {"status":"ok"}

# Login
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana","password":"..."}'
```

Luego abre la URL de Amplify y valida el flujo: login → venta → stock → reporte.

## Costos (orientativo)

- **Lambda + HTTP API**: pago por request; para una tienda pequeña, prácticamente
  dentro de capa gratuita.
- **DynamoDB on-demand**: pago por lectura/escritura; sin throughput provisionado.
- **Amplify Hosting**: build minutes + almacenamiento + transferencia.

Revisa la calculadora de precios de AWS para tu región antes de publicar en
producción.

## Seguridad

- El secreto JWT vive en **SSM SecureString**, nunca en el repo.
- Las contraseñas se almacenan con **bcrypt**.
- La función Lambda recibe permisos mínimos: CRUD sobre la tabla `pos` y lectura
  del parámetro SSM del secreto (ver `Policies` en `template.yaml`).
