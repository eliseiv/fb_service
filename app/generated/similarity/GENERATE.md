Generate similarity code from `datcat\microservices\facebook_service\` directory
`python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. ./app/generated/similarity/similarity.proto`
