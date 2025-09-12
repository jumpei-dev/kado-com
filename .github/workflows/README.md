# GitHub Actions ワークフロー

このディレクトリには、バッチ処理を自動化するためのGitHub Actionsワークフローが含まれています。

## ワークフローファイル

### 1. `batch-job.yml` - 基本バッチ処理

**実行スケジュール:**
- 稼働率計算: 毎日日本時間12時（UTC 3時）
- 稼働状況取得: 30分ごと
- 手動実行も可能

**実行可能なジョブ:**
- `status-collection`: 稼働状況データの収集
- `working-rate-calculation`: 稼働率の計算
- `debug-html`: HTMLファイルのデバッグ処理

### 2. `advanced-batch.yml` - 高度なバッチ処理

**追加機能:**
- マトリックス実行による並行処理
- エラーハンドリングとログ管理
- データベース接続テスト
- ヘルスチェック機能
- クリーンアップ処理

**実行スケジュール:**
- 稼働率計算: 毎日日本時間12時
- 稼働状況取得: 30分ごと
- ヘルスチェック: 15分ごと
- クリーンアップ: 毎日日本時間午前2時

## 必要なGitHub Secrets

以下のSecretsをGitHubリポジトリに設定する必要があります:

```
DATABASE_URL          # データベース接続URL
DB_PASSWORD           # データベースパスワード
AUTH_SECRET_KEY       # 認証用秘密鍵
X_BEARER_TOKEN        # X API Bearer Token
X_API_KEY             # X API Key
X_API_SECRET          # X API Secret
X_ACCESS_TOKEN        # X Access Token
X_ACCESS_TOKEN_SECRET # X Access Token Secret
```

## 手動実行方法

1. GitHubリポジトリのActionsタブに移動
2. 実行したいワークフローを選択
3. "Run workflow"ボタンをクリック
4. 必要なパラメータを選択して実行

## ログとアーティファクト

- 実行ログは各ワークフロー実行の詳細で確認可能
- バッチ処理のログファイルはアーティファクトとしてアップロード
- エラー発生時は詳細なログが保存される

## トラブルシューティング

### よくある問題

1. **データベース接続エラー**
   - `DATABASE_URL`と`DB_PASSWORD`の設定を確認
   - ネットワーク接続の問題がないか確認

2. **X API認証エラー**
   - X APIの各種トークンが正しく設定されているか確認
   - APIの利用制限に達していないか確認

3. **依存関係のエラー**
   - `batch/requirements.txt`が最新であることを確認
   - Pythonバージョンの互換性を確認

### ログの確認方法

1. Actions実行履歴から該当の実行を選択
2. 失敗したジョブをクリック
3. 各ステップのログを展開して詳細を確認
4. アーティファクトからバッチ処理のログファイルをダウンロード

## 設定のカスタマイズ

### スケジュールの変更

`cron`式を変更してスケジュールを調整できます:

```yaml
schedule:
  - cron: '0 3 * * *'  # 毎日UTC 3時（日本時間12時）
  - cron: '*/30 * * * *'  # 30分ごと
```

### タイムアウトの調整

```yaml
timeout-minutes: 30  # ジョブ全体のタイムアウト
```

### 環境変数の追加

```yaml
env:
  CUSTOM_ENV_VAR: ${{ secrets.CUSTOM_SECRET }}
```

## セキュリティ考慮事項

- 機密情報は必ずGitHub Secretsを使用
- ログに機密情報が出力されないよう注意
- 最小権限の原則に従ってアクセス権限を設定
- 定期的にSecretsの更新を実施