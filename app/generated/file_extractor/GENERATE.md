Generate similarity code from `datcat\microservices\yellowpage_service` directory
`python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. ./app/generated/file_extractor/extractor.proto`
