# Step 1：日本語の指示で動くROS 2 × Gazeboロボット

Physical AI 応用1の最終課題向けの小さなシミュレーションです。
日本語の指示を機械学習で分類し、差動二輪ロボットを3地点へ移動させます。
床の目印への移動までが対象で、点検・物品取得・トイレ清掃そのものは未実装です。

初めて読む方は [仕組みの簡潔な解説](はじめに_仕組みの簡潔な解説.md) をご覧ください。

## 起動と再実行（Windows PowerShell）

Docker DesktopをLinuxコンテナモードで起動し、このフォルダで実行します。

```powershell
.\run.ps1 start
.\run.ps1 demo
```

初回はDockerイメージの取得と構築に時間がかかります。結果は `output/` に保存されます。
再実行すると動画・モデル・評価結果・走行ログを更新します。残したい場合は先にコピーしてください。
既存の別プロジェクトのコンテナには触れません。

Notebookは http://127.0.0.1:8889 で開けます。
表示されたJupyter URLのポートを8888から8889に置き換え、トークンを使ってログインしてください。
トークンの確認は `docker compose exec -T sim python3 -m notebook list` です。
トークンは公開リポジトリや動画に含めないでください。
`Step1.ipynb` を上から順に実行すると、学習・推論・走行・動画・軌跡を確認できます。
通常のColabではこのNotebookだけでGazeboを起動できません。本Docker環境を使います。

停止は `.\run.ps1 stop`。成果物はホスト側に残ります。

PDFを再生成する場合は、ReportLabを使えるPython環境で
`python -m pip install -r requirements-report.txt`、`python scripts/make_report.py` を実行します。
先に `docker compose exec -T sim python3 scripts/verify_results.py` で走行結果を検証してください。
日本語フォントはWindowsのMS Gothicを埋め込み、他の環境ではCIDフォントを使用します。
提出用のタイトル・概要欄・手順は `SUBMISSION_53772.md` にまとめています。

## 動作の仕組み

1. ROS 2の `/instruction` に日本語の指示を送信。
2. TF-IDF（文字1～3-gram）＋ロジスティック回帰で4クラスを推論。
3. 点検 `(2,0)`、備品 `(2,1.8)`、ホーム `(0,0)` へ移動。停止指示も対応。
4. `/odom` に応じた比例制御で `/cmd_vel` を発行。`ros_gz_bridge` がGazeboへ転送。
   `/odom` はGazeboのOdometryPublisherが出力するシミュレータ内の実位置です。
   車輪回転からの推定値は `/wheel_odom` に分離。自己位置推定の誤差を除いた初歩的な条件です。
5. 目的地との距離が0.10 m未満になったら停止。
6. Gazebo仮想カメラの実画像に推論・座標を重ね、MP4として記録。

AIは40文の自作学習データで学習し、学習に使わない8文で確認します。
未知指示は分類スコア0.60未満なら停止します。これは万能な未知指示判定ではありません。
否定や複数命令を含む自由な日本語、障害物回避、SLAM、動的な経路計画は対象外です。
オドメトリが1秒以上途絶えたときも速度ゼロを送ります。ただし制御プロセス自体が落ちた場合の
モータ側ウォッチドッグは未実装です。実機への利用を想定した安全機能ではありません。

## ファイル

|ファイル|役割|
|---|---|
|`Step1.ipynb`|学習と再実行の入口|
|`scripts/intent_model.py`|学習データ・AIモデル・分類評価|
|`scripts/controller.py`|ROSノード・移動制御・録画|
|`scripts/run_demo.py`|Gazeboとブリッジを起動してデモ実行|
|`scripts/make_world.py` / `world/step1.sdf`|独自の二輪ロボットと床面のモデル|
|`config/bridge.yaml`|ROS 2とGazeboの接続|
|`output/demo.mp4`|シミュレーション動画|
|`output/run_result.json`|実走行の成否・到着誤差・指示履歴|
|`output/intent_evaluation.json`|分類モデルの評価|
|`output/trajectory.csv`|ROSオドメトリと速度指令|

## 手動で指示を送る

自動デモと同時には実行しないでください。コンテナ内のターミナルを3つ開き、各々で
`source /opt/ros/jazzy/setup.bash` を実行してから以下を実行します。

```bash
# ターミナル1
gz sim -r world/step1.sdf
# ターミナル2
ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=/work/config/bridge.yaml
# ターミナル3
python3 scripts/controller.py
# さらに別のターミナルから指示
ros2 topic pub --once /instruction std_msgs/msg/String "{data: '点検エリアへ移動してください'}"
```

GUIは http://127.0.0.1:6080/vnc.html から確認できます。
終了時は各ターミナルでCtrl+C。通常のデモはGUIを開かず仮想カメラで録画します。

## 提出チェック（課題PDF 10/19改訂版に基づく）

- [ ] 自分で動画を見て、コードとAIの役割を説明できることを確認。
- [ ] 動画はMP4で1～3分。倍速なら明記。本デモは実時間収録。
- [ ] 説明PDFを `説明資料_PAI最終課題_<OmniCampusアカウント名またはID>.pdf` に変更。
- [ ] 本フォルダのコード一式をGitHubの**public**リポジトリへ公開。
- [ ] 動画を自分のYouTubeへ**限定公開以上**でアップロード。
- [ ] 動画タイトルは `PAI最終課題_<OmniCampusアカウント名またはID>`。
- [ ] 氏名・所属・メール・トークンが入っていないことを確認。
- [ ] OmniCampusに説明PDF・GitHub URL・YouTube URLを提出。
- [ ] 締切：2026年11月2日（月）午前10:00（講座資料の表記）。

YouTube・GitHubへの公開やOmniCampusへの提出は、ローカルでの作成だけでは完了しません。
合否は講座運営の判断です。

## 参考と独自部分

- 講座指定の参考： https://qiita.com/N622/items/9d89f77d85d9da0af29e
- 公式の組み合わせ： https://gazebosim.org/docs/harmonic/ros_installation/
- 差動二輪の公式解説： https://gazebosim.org/docs/harmonic/moving_robot/
- ROSブリッジ： https://github.com/gazebosim/ros_gz/tree/jazzy/ros_gz_bridge
- 実位置の取得： https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1OdometryPublisher.html

参考記事のROS 2 Humble / Fortressの概念を参考に、Jazzy / Harmonicで独自に実装。
参考記事のCADモデルやC++コードはコピーしていません。
日本語分類AI、3地点の自律移動、未知指示の停止、到着誤差と映像の記録が追加部分です。
コード・文章の作成には生成AI（Codex）を使用しています。実行時のAIはロジスティック回帰です。
Docker内では小さなモデルをCPUで学習し、描画もソフトウェア描画です。GPUや外部APIは不要です。

## 今後（今回の範囲外）

Step 2では指示文・目的地・速度を変えて比較。Step 3ではトイレの床を想定した
走行範囲の網羅や障害物回避など一点に絞って、清掃動作へ段階的に発展させます。
