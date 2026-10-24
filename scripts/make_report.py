"""Build the submission PDF from actual recorded results. Requires reportlab."""
import json
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output'
run=json.loads((OUT/'run_result.json').read_text(encoding='utf-8'))
ai=json.loads((OUT/'intent_evaluation.json').read_text(encoding='utf-8'))
check=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
assert run['success'] and check['passed'], 'Do not write a successful report without verified evidence'
font_path=Path('C:/Windows/Fonts/msgothic.ttc')
if font_path.exists():
    pdfmetrics.registerFont(TTFont('Japanese',str(font_path),subfontIndex=0)); font='Japanese'
else:
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5')); font='HeiseiKakuGo-W5'
navy=colors.HexColor('#17324d'); teal=colors.HexColor('#167a93')
styles={
 'title':ParagraphStyle('title',fontName=font,fontSize=20,leading=28,textColor=navy,spaceAfter=12,wordWrap='CJK'),
 'h':ParagraphStyle('h',fontName=font,fontSize=12,leading=18,textColor=teal,spaceBefore=12,spaceAfter=6,wordWrap='CJK'),
 'p':ParagraphStyle('p',fontName=font,fontSize=9.7,leading=16,spaceAfter=7,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName=font,fontSize=8,leading=12,spaceAfter=5,wordWrap='CJK'),
}
story=[]
def p(text,style='p'): story.append(Paragraph(text,styles[style]))
def table(rows,widths):
    t=Table([[Paragraph(str(c),styles['small']) for c in row] for row in rows],colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f0f5')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#c7d6de')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)])); story.append(t)

p('日本語の指示で移動する<br/>ROS 2 × Gazeboロボット','title')
p('Physical AI 応用1 最終課題 ｜ OmniCampus ID：53772 ｜ 2026年10月24日','small')
p('1. 課題の目的と対象','h')
p('初歩的なROS 2とGazeboの連携を基礎に、日本語で指定した地点へロボットが自律移動する仕組みを実装した。すべてシミュレーション内で実行し、点検地点・備品地点・ホームを巡回する。各地点は床の目印であり、実際の点検、備品取得、清掃作業は行わない。')
p('2. システム構成とAIの役割','h')
p('日本語指示 → 文字TF-IDF＋ロジスティック回帰 → 目的地選択 → ROS 2の速度指令 → ros_gz_bridge → Gazeboの差動二輪ロボット。Gazeboの実位置（OdometryPublisher）をROS 2で受信し、目標との距離が0.10 m未満になれば停止する。')
p('実行時のAIは指示文の分類を担う。自作の40文から「点検」「備品」「ホーム」「停止」の4クラスを学習した。走行は比例制御であり、走行動作自体の強化学習やLLM推論は行っていない。分類スコアが0.60未満なら未対応として停止する。')
p('環境：ローカルPCのDocker Desktop内、Ubuntu 24.04 / ROS 2 Jazzy / Gazebo Harmonic。Python・scikit-learn・rclpyを使用。最大速度0.24 m/s。CPUで学習・ソフトウェア描画を実行。動画は1280×800、10 fps。','small')
p('3. 実際のシミュレーション画面','h')
story.append(Image(str(OUT/'arrival_supply.png'),width=440,height=275))
p('図1：備品地点への到着。映像はGazeboの仮想カメラが出力した画像を使用。右側にはAIの分類結果、速度指令、ROSオドメトリを表示した。','small')
story.append(PageBreak())
p('検証結果・工夫・考察','title')
p('4. 実行結果','h')
names={'inspection':'点検地点','supply':'備品地点','home':'ホーム'}
table([['目的地','目標座標 [m]','到着誤差 [m]','結果']]+[[names[g['intent']],{'inspection':'(2.0, 0.0)','supply':'(2.0, 1.8)','home':'(0.0, 0.0)'}[g['intent']],f"{g['error_m']:.4f}",'到着・停止'] for g in run['goals']], [110,150,130,113])
p(f"3地点すべてで到着条件を満たした。提出動画は{run['video_duration_s']:.1f}秒、実時間収録で倍速編集はしていない。カメラ画像を{run['camera_messages']}件受信し、軌跡と指示履歴をCSV・JSONに保存した。")
p(f"学習に使わない自作の8文は{ai['correct']}/8で正しく分類した。「こんにちは」「明日の天気は」「ダンスを踊って」の3例は未対応と判定した。デモでは帰還後の未対応指示・停止指示に対して速度ゼロを継続し、その間の位置変化は{check['stationary_drift_m']:.5f} mだった。これは限られた文例と1回の走行の結果である。")
p('5. 参考サンプルから追加した独自の工夫','h')
p('参考サンプルの基本であるROS 2とGazeboの速度指令の連携に対し、①日本語分類AI、②オドメトリによる3地点への自律移動と停止、③低スコアの指示の棄却、④映像と数値ログによる確認、⑤Notebookからの再実行を追加した。ロボットの形状、床面、制御コードは独自に作成し、参考記事のCADモデルやC++コードはコピーしていない。')
p('6. 限界と今後の発展','h')
p('評価文は学習文に近い語彙であり、一般的な日本語理解を示すものではない。否定表現、複数命令、未知指示の全般的な検出は未検証。シミュレータの実位置を利用する理想的な自己位置認識を前提とし、SLAM・障害物回避・清掃マニピュレーションは未実装。オドメトリ受信が途絶えた際は停止指令を送るが、制御プロセス停止時のモータ側ウォッチドッグは備えていない。')
p('次の段階では、指示の言い換え、速度、目的地を一つずつ変えて比較する。その後、トイレ清掃を想定し、床面の走行範囲の網羅や障害物回避など、対象を一つに絞って検証する。')
p('7. 参考資料・生成AIの利用','h')
for text,url in [('講座指定：gazeboとROS2を連携してロボットを操作する','https://qiita.com/N622/items/9d89f77d85d9da0af29e'),('Gazebo公式：ROSとGazeboの組み合わせ','https://gazebosim.org/docs/harmonic/ros_installation/'),('Gazebo公式：差動二輪ロボット','https://gazebosim.org/docs/harmonic/moving_robot/')]:
    p(f'{text}<br/><link href="{url}" color="#167a93">{url}</link>','small')
p('課題条件は「最終課題（10_19 改訂版）」を参照。コードと説明資料の作成には生成AI（Codex）を利用した。実行結果はローカルのシミュレーションから取得した。','small')
def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#c7d6de')); canvas.line(46,39,549,39)
    canvas.setFont(font,8); canvas.setFillColor(navy); canvas.drawString(46,26,'PAI 最終課題 | 53772 | シミュレーションによる検証'); canvas.drawRightString(549,26,str(doc.page))
path=OUT/'説明資料_PAI最終課題_53772.pdf'
SimpleDocTemplate(str(path),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=38,bottomMargin=52,title='PAI最終課題_53772',author='53772').build(story,onFirstPage=footer,onLaterPages=footer)
print(path)
