# ローカルGitの使い方

このフォルダのコードと成果物の変更履歴をGitで保存します。
GitHubへのアップロードとは別の操作です。

PowerShellでこのフォルダを開いてください。

```powershell
cd C:\Users\aujoy\Desktop\otani\dev\matsuo_dev\physical_ai_step1
```

## まず使うコマンド

```powershell
# 変更したファイルを確認
git status

# 未登録の変更内容を確認（新規ファイルの本文は表示されません）
git diff

# 例：説明ガイドの変更を次の保存対象に登録
git add -- はじめに_仕組みの簡潔な解説.md

# 保存対象を確認
git diff --cached --stat

# 変更履歴を保存
git commit -m "Update beginner guide"

# 過去の保存履歴を確認
git log --oneline -5

# 登録されたGitHubの送信先を確認（通信はしません）
git remote -v
```

`git add` は保存対象の選択、`git commit` はPC内への履歴保存です。
動画やPDFを更新した場合も、必要なファイルを選んで登録してください。
実行ログ・Notebookの一時ファイル・環境変数ファイルなどは `.gitignore` で除外しています。

## このリポジトリの設定

- ブランチ：`main`
- 送信先 `origin`：`https://github.com/uwasanok/physical-ai-learn-2026-001.git`
- コミット名：`uwasanok`
- コミット用メール：`uwasanok@users.noreply.github.com`（個人のメールアドレスは使用しません）

名前とメールはこのリポジトリだけに設定します。他のプロジェクトの設定は変更しません。
これは履歴上の作成者表示であり、GitHubのログイン設定ではありません。

## GitHubへの反映について

送信先URLの登録だけではアップロードされません。認証と接続確認は未実施です。
GitHub側の既存ファイルや履歴も未確認のため、最初の送信前に確認して統合する必要があります。
履歴が食い違った場合、強制pushで上書きせず、既存の内容を残して統合してください。
