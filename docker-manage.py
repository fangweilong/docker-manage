import docker
import os
import sys

client = docker.DockerClient(base_url='unix://var/run/docker.sock')

containerName = sys.argv[1]

imageName = sys.argv[2]

imageFilePath = sys.argv[3]

thisCwd = os.path.split(os.path.realpath(__file__))[0]


def removeContainer():
    # 移除容器
    try:
        containers = client.containers.get(containerName)
        containers.stop()
        containers.remove()
        print("移除容器")
    except Exception as e:
        print(e)

def removeImages():
    # 移除镜像
    try:
        client.images.remove(imageName)
        print("移除镜像")
    except Exception as e:
        print(e)

def loadImage():
    # 加载镜像
    imageFile = None
    try:
        imageFile = open(imageFilePath, 'rb')
        client.images.load(imageFile)
    except Exception as e:
        print(e)
    finally:
        imageFile.close()

def start():
    # 启动镜像
    try:
        print("启动"+thisCwd+"镜像")
        os.system("cd "+thisCwd+" && docker-compose up -d")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    removeContainer()
    removeImages()
    loadImage()
    start()