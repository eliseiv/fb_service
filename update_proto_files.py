import os
from pathlib import Path
from typing import List

import grpc
import subprocess

from app.domain.utils.logutils import init_logger
from app.infrastructure.settings import GRPC_HOST, GRPC_PORT, LOG_DIR, APP_DIR, BASE_DIR

from app.generated.renewer import renewer_pb2, renewer_pb2_grpc

logger = init_logger(filename='facebook.log', logdir=LOG_DIR)

class ProtoHandler:
    def __init__(self):
        self.GEN_DIR = os.path.join(APP_DIR, 'generated')

    def scan(self):
        updated = False
        try:
            names = self.__get_required_proto_names
            for name in names:
                response = self.get_proto_content(name)
                if response.get('status') == 'success':
                    server_side_proto = response.get('content')
                    local_side_proto = self.read_file_content(name)
                    if not self.identical_contents(server_side_proto, local_side_proto):
                        self.correct_proto(name, server_side_proto)
                        updated = True
                else:
                    logger.error(response.get('content'))
            if not updated:
                logger.info('Nothing to update')
        except Exception as e:
            logger.error(e)

    def correct_proto(self, name: str, server_side_proto: str):
        try:
            self.update_file_content(name, server_side_proto)
            PROTO_D = os.path.abspath(Path(self.GEN_DIR) / name)
            PROTO_F = next((p.name for p in Path(PROTO_D).glob("*.proto")), None)
            logger.info(f'Detected updates for {name}/{PROTO_F}')
            self.__generate_new_files(name, PROTO_F)
        except Exception as e:
            logger.error(e)

    @staticmethod
    def get_proto_content(name: str):
        with grpc.insecure_channel(f'{GRPC_HOST}:{GRPC_PORT}') as channel:
            stub = renewer_pb2_grpc.RenewServiceStub(channel)
            response = stub.Renew(renewer_pb2.RenewRequest(name=name))

        return response.content

    @staticmethod
    def identical_contents(cont1: str, cont2: str) -> bool:
        if cont1 == cont2:
            return True
        return False

    def read_file_content(self, proto_name: str) -> str:
        """
        Read the content of a file.
        :param proto_name: File path
        """
        content = ''
        try:

            PROTO_D = os.path.abspath(Path(self.GEN_DIR) / proto_name)
            PROTO_F = next(Path(PROTO_D).glob("*.proto"), None)

            with open(PROTO_F, mode="r", encoding='utf8', errors='replace') as f:
                content = f.read()

        except IOError as e:
            logger.error(e)

        return content

    def update_file_content(self, proto_name: str, content: str) -> None:
        """
        Write content in to a file.
        :param proto_name: File path
        :param content: data to be written.
        """
        try:
            PROTO_D = os.path.abspath(Path(self.GEN_DIR) / proto_name)
            PROTO_F = next(Path(PROTO_D).glob("*.proto"), None)

            with open(PROTO_F, mode="w", encoding='utf8', errors='replace') as f:
                f.write(content)

        except IOError as e:
            logger.error(e)

    @property
    def __get_required_proto_names(self) -> List[str]:
        return [d.name for d in Path(self.GEN_DIR).iterdir() if d.is_dir() and d.name != "__pycache__"]

    @staticmethod
    def __generate_new_files(p_dir: str, p_name: str):
        script = (f"cd {BASE_DIR} && python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. "
                  f"./app/generated/{p_dir}/{p_name}")

        try:
            result = subprocess.run(script, shell=True, check=True, capture_output=True, text=True)
            logger.info(f"Files generated for: {p_dir}/{p_name}: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing command: {e.stderr}")


if __name__ == '__main__':
    ProtoHandler().scan()