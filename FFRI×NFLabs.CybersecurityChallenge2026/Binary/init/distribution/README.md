# 動作検証手順

1. `docker compose up` を実行して、Dockerイメージのビルドや、Dockerコンテナの実行を行います。
    - このとき`compose.yml`の内容により、ホストの`24634/tcp`がDockerコンテナの`24634/tcp`と紐づけられます。
2. `nc localhost 24634` などを実行して、Dockerコンテナを実行しているホストへ接続し、問題へ挑みます。
