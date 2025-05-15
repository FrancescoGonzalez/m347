FROM codercom/code-server:latest

USER root

RUN apt-get update && apt-get install -y openjdk-17-jdk

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

EXPOSE 8080

USER coder

WORKDIR /home/coder/project

RUN code-server --install-extension vscjava.vscode-java-pack

ENTRYPOINT ["/usr/bin/entrypoint.sh", "--bind-addr", "0.0.0.0:8080", "."]