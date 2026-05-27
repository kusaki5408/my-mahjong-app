import os, time, re
from google import genai
from google.genai import types
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

st.set_page_config(page_title="AI麻雀戦術論クイズ", page_icon="💻", layout="centered")
st.title("🀄️ AIが考える　麻雀最強理論　クイズ！")
st.caption("最新AIはこう考えます！")
st.write("---")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
models_to_try = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview"
]

# 🏫 ボケ選択肢の禁止を徹底したプロンプト
mahjong_config = types.GenerateContentConfig(
    system_instruction="""あなたは現代麻雀の最強思考法を教えるAI先生です。
    具体的な麻雀牌を使った手牌の文字列は、絶対に【一切出力しないで】ください。
    「戦術論」「押し引きの基準」「期待値」「マインドセット」に関する4択クイズをテンポよく1問ずつ出題してください。
    
    【厳格なルール】
    1. 【ボケ・おふざけ回答の完全禁止】4つの選択肢（A, B, C, D）はすべて、実戦の戦術としてあり得る「大真面目で論理的な選択肢」にしてください。精神論、オカルト、ウケ狙いのボケは絶対に排除してください。
    2. 前置きや解説はすべて「短く簡潔に」3行程度でわかりやすくまとめてください。
    3. 問題文は「〇〇な状況での押し引きの基準は？」や「デジタル麻雀における期待値の考え方は？」といった、理論・セオリーに関する記述にしてください。
    4. 「期待値」という言葉を使わないでください。
    
    【出力テンプレート】
    戦術テーマ：[例：ベタオリ時の安全度比較など]
    
    問題文：[戦術に関する論理的な問いを1文で記述]
    
    [A: 〇〇という選択] [B: 〇〇という選択] [C: 〇〇という選択] [D: 〇〇という選択]
    
    4. ユーザーが回答してきたら、最初に「正解！」か「不正解！」かをハッキリ伝え、データや論理に基づいた解説を3行以内でコンパクトに記述してください。
    5. ユーザーの回答が不正解だった場合、「AIの考える正解」を伝えてください。
    6. 解説が終わったら、すぐに次の真面目な戦術論クイズと選択肢を出力してください。
    7. 5〜6問で終了する際は、メッセージの末尾に【クイズ終了】と書いてください。
    """
)

def get_gemini_response(user_input_now=None):
    formatted_contents = []
    for msg in st.session_state.mahjong_history:
        formatted_contents.append(types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["content"])]))
    if user_input_now:
        formatted_contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input_now)]))
    if not formatted_contents:
        formatted_contents = ["「麻雀戦術論クイズスタート！」と言って、真面目な最初のクイズを出題してください。"]

    for model_name in models_to_try:
        try:
            return client.models.generate_content(model=model_name, contents=formatted_contents, config=mahjong_config).text.strip()
        except:
            time.sleep(1)
    return None

# --- 🧠 セッション初期化 ---
if "mahjong_history" not in st.session_state:
    st.session_state.mahjong_history, st.session_state.mahjong_options = [], {}

if len(st.session_state.mahjong_history) == 0:
    with st.spinner("思考ロジックを構築中..."):
        first_quiz = get_gemini_response()
        if first_quiz: st.session_state.mahjong_history.append({"role": "assistant", "content": first_quiz})

# 📱 画面の描画処理
for msg in st.session_state.mahjong_history:
    clean_content = re.sub(r'\[[A-D]:.*?\]', '', msg["content"]).strip()
    clean_content = clean_content.replace("【クイズ終了】", "").strip()
    st.chat_message(msg["role"]).write(clean_content)

st.write("---")

is_quiz_ended = False
if st.session_state.mahjong_history:
    last_text = st.session_state.mahjong_history[-1]["content"]
    if "【クイズ終了】" in last_text:
        is_quiz_ended = True
    else:
        matches = re.findall(r'\[([A-D]):\s*(.*?)\]', last_text)
        st.session_state.mahjong_options = {r: t for r, t in matches} if matches else {}

# 📥 4択ボタンの配置
if is_quiz_ended:
    st.success("🎉 すべての戦術論クイズをクリアしました！")
    if st.button("もう一度挑戦する 🔄", use_container_width=True):
        st.session_state.mahjong_history, st.session_state.mahjong_options = [], {}
        st.rerun()
elif st.session_state.mahjong_options:
    st.write("**👇 正しい現代麻雀のセオリーを選択しよう！** ")
    cols = st.columns(4)
    user_choice = None
    
    keys = ["A", "B", "C", "D"]
    for i in range(len(keys)):
        k = keys[i]
        txt = st.session_state.mahjong_options.get(k, k)
        with cols[i]:
            if st.button(txt, use_container_width=True): user_choice = k

    if user_choice:
        chosen_text = st.session_state.mahjong_options.get(user_choice, user_choice)
        user_message = f"私は「{chosen_text}」の思考法を支持します。"
        st.session_state.mahjong_history.append({"role": "user", "content": user_message})
        with st.spinner("理論を照合中..."):
            res_text = get_gemini_response(user_message)
            if res_text:
                st.session_state.mahjong_history.append({"role": "assistant", "content": res_text})
                st.rerun()
else:
    if st.button("新しくやり直す 🔄", use_container_width=True):
        st.session_state.mahjong_history, st.session_state.mahjong_options = [], {}
        st.rerun()
