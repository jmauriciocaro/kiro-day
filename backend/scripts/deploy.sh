#!/usr/bin/env bash
# Despliegue del backend del POS con AWS SAM.
#
# Requisitos (NO incluidos en el repo):
#   - AWS SAM CLI instalado      (https://docs.aws.amazon.com/serverless-application-model/)
#   - AWS CLI configurado con credenciales válidas (aws configure / SSO / rol)
#
# Uso:
#   ./scripts/deploy.sh [stack-name] [region]
#
# El script es idempotente: crea el secreto JWT en SSM solo si no existe.
set -euo pipefail

STACK_NAME="${1:-pos-mvp}"
REGION="${2:-${AWS_REGION:-us-east-1}}"
JWT_PARAM="/pos/jwt-secret"

echo "==> Despliegue del backend POS"
echo "    Stack:  $STACK_NAME"
echo "    Región: $REGION"

# --- Comprobaciones previas ------------------------------------------------
if ! command -v sam >/dev/null 2>&1; then
  echo "ERROR: AWS SAM CLI no está instalado." >&2
  echo "       Instálalo: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html" >&2
  exit 1
fi

if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
  echo "ERROR: no hay credenciales AWS válidas (aws sts get-caller-identity falló)." >&2
  echo "       Configura credenciales con 'aws configure' o un rol/SSO antes de desplegar." >&2
  exit 1
fi

# --- Secreto JWT en SSM (solo si no existe) --------------------------------
if aws ssm get-parameter --name "$JWT_PARAM" --region "$REGION" >/dev/null 2>&1; then
  echo "==> Secreto JWT ya existe en SSM ($JWT_PARAM), se reutiliza."
else
  echo "==> Creando secreto JWT en SSM ($JWT_PARAM) como SecureString."
  aws ssm put-parameter \
    --name "$JWT_PARAM" \
    --type SecureString \
    --value "$(openssl rand -hex 32)" \
    --region "$REGION"
fi

# --- Build + deploy --------------------------------------------------------
echo "==> sam build"
sam build

echo "==> sam deploy"
sam deploy \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

echo
echo "==> Despliegue completado. URL del API:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text

echo
echo "Siguiente paso: usa esa URL como VITE_API_URL en Amplify Hosting,"
echo "y siembra usuarios con scripts/seed_users.py apuntando a la región desplegada."
