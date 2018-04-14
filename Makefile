STACKNAME_BASE="s3-bucket-default-encrypter"
REGION="us-east-2"
# Bucket in REGION that is used for deployment
BUCKET=$(STACKNAME_BASE)
MD5=$(shell md5sum lambda/*.py | md5sum | cut -d ' ' -f 1)

deploy:
	cd lambda && \
		zip -r9 /tmp/deployment.zip *.py && \
		aws s3 cp --region $(REGION) /tmp/deployment.zip \
			s3://$(BUCKET)/$(MD5).zip && \
		rm -rf /tmp/deployment.zip
	aws cloudformation deploy \
		--template-file deployment.yml \
		--stack-name $(STACKNAME_BASE) \
		--region $(REGION) \
		--parameter-overrides \
		"Bucket=$(BUCKET)" \
		"md5=$(MD5)" \
		--capabilities CAPABILITY_IAM || exit 0
