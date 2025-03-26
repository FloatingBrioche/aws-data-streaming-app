FROM public.ecr.aws/lambda/python:3.12

COPY layer_requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install -r layer_requirements.txt

COPY lambda_app/*.py ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.lambda_handler" ]