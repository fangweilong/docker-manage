import os
import subprocess
import paramiko
import yaml

# 当前路径
from paramiko.ssh_exception import NoValidConnectionsError, AuthenticationException

DIR = os.path.abspath(os.path.dirname(__file__))
# 运行的主路径
dockerBuildPath = DIR + "../../../"


# 执行命令行
def executeCommand(com):
    print("执行语句：\n", com)
    print("查看执行信息：\n")
    ex = subprocess.Popen(com, stdout=subprocess.PIPE, shell=True)
    out, err = ex.communicate()
    status = ex.wait()


# 打包
def build():
    # 获取所有文件夹和文件
    for path in os.listdir(dockerBuildPath):
        buildPath = os.path.normpath(dockerBuildPath + path)
        print("当前工作目录：", buildPath)
        if os.path.isdir(buildPath):
            print(buildPath + "是文件夹，检查其他条件")
            if CheckFileIsDocker(buildPath):
                print("满足打包条件，等待打包。。。")
                ymlPath = os.path.normpath(buildPath + "/docker-compose.yml")
                cmdStr = "docker-compose -f " + ymlPath + " build"
                print("执行打包语句：", cmdStr)
                cmdResult = os.popen(cmdStr).readlines()
                print("请查看返回信息，检阅打包成果：\n", cmdResult)
                print("打包操作完成==================")
            else:
                print("不满足条件，跳过打包。\n")
        else:
            print(buildPath + "不是文件夹，跳过docker-build\n")


# 检查docker build的基本条件是否存在
# 需要target、DockerFile、docker-compose.yml文件夹同时存在
def CheckFileIsDocker(path):
    targetPath = path + "/target"
    if os.path.exists(targetPath):
        print("有target 需要打包")
        jarCount = 0
        for file in os.listdir(targetPath):
            if file.endswith(".jar"):
                jarCount += 1
        if jarCount > 0:
            print("有jar 需要打包")
        else:
            print("没有jar 不需要打包")
            return False
    else:
        print("没有target 不需要打包")
        return False

    if os.path.exists(path + "/DockerFile"):
        print("DockerFile存在")
    else:
        print("没有DockerFile 不需要打包")
        return False

    if os.path.exists(path + "/docker-compose.yml"):
        print("docker-compose.yml存在")
    else:
        print("没有docker-compose 不需要打包")
        return False

    return True


# 保存docker的编译文件
def saveDockerBuildFile():
    # 判断保存文件夹是否存在，如果不存在则创建
    savePath = dockerBuildPath + "docker-save-images"
    if not os.path.isdir(savePath):
        os.mkdir(savePath)

    print("镜像将保存在路径中：", savePath)

    # 获取所有文件夹和文件
    for path in os.listdir(dockerBuildPath):
        buildPath = os.path.normpath(dockerBuildPath + path)
        print("当前工作目录：", buildPath)
        if os.path.isdir(buildPath):
            if CheckFileIsDocker(buildPath):
                with open(buildPath + "/docker-compose.yml") as lines:
                    for line in lines:
                        lineStr = line.replace(" ", "")
                        if lineStr.startswith("image:"):
                            # 镜像名字
                            imageName = lineStr.replace("image:", "").replace(" ", "")
                            # 保存的包名
                            imageNameFormat = imageName.replace(":", "-").replace(".", "-") + ".tar"
                            cmdStr = "docker save -o {} {}".format(os.path.normpath(savePath + "/" + imageNameFormat),
                                                                   imageName).replace("\r\n", "").replace("\n", "")
                            executeCommand(cmdStr)
        else:
            print(buildPath + "不是文件夹，跳过保存检查\n")


# 上传image到服务器上
def uploadDockerImageToServer():
    # 读取配置文件
    file = open(DIR + "/config.yaml", 'r', encoding="utf-8")
    yamlTemp = yaml.load(file, Loader=yaml.Loader)

    putFile(yamlTemp)


# 上传文件
def putFile(yamlTemp):
    linuxLink = None
    sftp = None

    try:
        # 链接到sftp
        linuxLink = paramiko.Transport(yamlTemp["host"], yamlTemp["port"])
        linuxLink.connect(username=yamlTemp["username"], password=yamlTemp["password"])
        sftp = paramiko.SFTPClient.from_transport(linuxLink)
        remotePath = yamlTemp["upload"]["remote-path"]
        # 是否需要建立目录
        try:
            sftp.chdir(remotePath)
        except Exception as e:
            sftp.mkdir(remotePath)

        print(remotePath)
        for localConfig in yamlTemp["upload"]["file"]:
            sftp.put(os.path.abspath(localConfig["local-path"]), remotePath + localConfig["remote-file"])

            execCmd(yamlTemp, localConfig["cmd"])
    except Exception as e:
        print(e)

    finally:
        print("关闭sftp链接...")
        sftp.close()
        print("关闭ssh链接...")
        linuxLink.close()


def execCmd(yamlTemp):
    # 链接到linux
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(yamlTemp["host"], port=yamlTemp["port"], username=yamlTemp["username"],
                    password=yamlTemp["password"])
        stdin, stdout, stderr = ssh.exec_command(cmd)
        # 获取命令结果
        result = stdout.read()
        print(result)
    except NoValidConnectionsError:
        print('连接出现了问题')
    except AuthenticationException:
        print('用户名或密码错误')
    except Exception as e:
        print('其他错误问题{}'.format(e))
    finally:
        print("关闭ssh连接...")
        ssh.close()


if __name__ == "__main__":
    num = input("请输入数字:\n"
                "   1.build\n"
                "   2.保存为.tar\n"
                "   3.上传.tar\n")
    if num == "1":
        # 编译
        build()
    elif num == "2":
        # 保存
        saveDockerBuildFile()
    elif num == "3":
        # 上传文件
        uploadDockerImageToServer()
    else:
        print("请输入本程序支持的数字")