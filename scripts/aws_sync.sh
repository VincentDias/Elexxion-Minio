mc alias set minio-local http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
mc alias set aws-s3 https://s3.eu-west-1.amazonaws.com $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY

while true; do
  echo "[`date +'%Y-%m-%d %H:%M:%S'`] Début synchronisation..."

  mc mirror \
    --overwrite \
    --remove \
    --region eu-west-1 \
    --watch \
    minio-local/elexxion-minio-bucket \
    aws-s3/elexxion-aws-bucket | while read line; do
      echo "✈️​ [`date +'%Y-%m-%d %H:%M:%S'`] $line"
  done

  echo "[`date +'%Y-%m-%d %H:%M:%S'`] Pause 60 s..."
  sleep 60
done
