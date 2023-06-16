# labmda用のスクリプトとレイヤー

## レイヤー
webhookを実行するための外部ライブラリであるslackwebをレイヤーとして追加
``` 
 pip install slackweb -t ./python --no-user
```
インストール後pythonフォルダを.zipしてアップロード
[レイヤー詳細](ttps://ap-northeast-1.console.aws.amazon.com/lambda/home?region=ap-northeast-1#/layers/slackweb_layer/versions/1?tab=versions)

labmda_function.pyには実際のlambda関数のソースをコピペして書いている。
lambdaを修正したらこのファイルを追従を忘れない。


