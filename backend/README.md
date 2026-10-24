# POS MVP — Backend (FastAPI + DynamoDB)

API del punto de venta. FastAPI (Python 3.12 en producción) sobre AWS Lambda vía
Mangum, detrás de un HTTP API de API Gateway, con una única tabla DynamoDB.

## Desarrollo local

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt

# Variables para desarrollo (NO usar en producción):
export POS_TABLE_NAME=pos
export POS_JWT_SECRET=dev-secret-solo-local   # en prod se lee de SSM
export AWS_REGION=us-east-1

uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000` (`/docs` para la UI de OpenAPI).

## Pruebas

```bash
. .venv/bin/activate
pytest -q
```

Los tests usan `moto` para simular DynamoDB; no tocan AWS real.

## Configuración (variables de entorno)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `POS_TABLE_NAME` | Nombre de la tabla DynamoDB | `pos` |
| `AWS_REGION` | Región AWS | `us-east-1` |
| `POS_JWT_SECRET_PARAM` | Nombre del parámetro SSM con el secreto JWT | `/pos/jwt-secret` |
| `POS_JWT_SECRET` | Override directo del secreto (solo dev/test) | — |
| `POS_JWT_TTL_SECONDS` | Vigencia del token | `3600` |
| `POS_DYNAMODB_ENDPOINT_URL` | Endpoint local de DynamoDB (opcional) | — |

> El secreto JWT nunca va en el repo. En producción se lee de SSM Parameter
> Store (SecureString). En local se puede usar `POS_JWT_SECRET`.

## Despliegue (AWS SAM)

Requiere AWS SAM CLI y credenciales configuradas.

```bash
# 1. Crear el secreto JWT en SSM (una sola vez):
aws ssm put-parameter --name /pos/jwt-secret --type SecureString \
  --value "$(openssl rand -hex 32)"

# 2. Construir y desplegar:
sam build
sam deploy --guided   # la primera vez; luego: sam deploy

# 3. Probar la API local con SAM (opcional):
sam local start-api
```

La salida `ApiUrl` del stack es la URL base del HTTP API; úsala como
`VITE_API_URL` en el frontend.

## Sembrar usuarios

Los usuarios (`cajero`, `dueño`) se guardan como ítems `USER#<username>` con la
contraseña en bcrypt. Un script de seed (o una llamada administrativa) crea los
usuarios iniciales; nunca se escriben credenciales en el repo.
