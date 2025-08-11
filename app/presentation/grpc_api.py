import grpc
from app.infrastructure.settings import GRPC_HOST, GRPC_PORT

from app.generated.similarity import similarity_pb2, similarity_pb2_grpc
from app.generated.file_extractor import extractor_pb2, extractor_pb2_grpc

class GRPC:
    @staticmethod
    def count_ratio_s(keyword: str, text: str):
        with grpc.insecure_channel(f'{GRPC_HOST}:{GRPC_PORT}') as channel:
            stub = similarity_pb2_grpc.SimilarityServiceStub(channel)
            response = stub.CountRatioS(similarity_pb2.CountRatioSRequest(substring=keyword, text=text))

        return response.ratio

    @staticmethod
    def get_proxies():
        with grpc.insecure_channel(f'{GRPC_HOST}:{GRPC_PORT}') as channel:
            stub = extractor_pb2_grpc.FileExtractorServiceStub(channel)
            response = stub.GetProxies(extractor_pb2.GetProxiesRequest())

        return response.proxies
