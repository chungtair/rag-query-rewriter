<div align="center">

# rag-query-rewriter

### Context-aware query rewriter for RAG systems
### RAG 上下文問題重寫器 — 解決多輪對話「找不到知識」的問題
### RAG 用 文脈考慮型クエリリライター

A minimal Python tool that rewrites follow-up questions into standalone queries — so your RAG retriever stops saying *"I don't know"* every time a user asks "How much is it?" or "Is it refundable?".

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![Chung Tair](https://img.shields.io/badge/by-Chung_Tair-orange)](https://chungtair.com)

**Languages:** [English](#english) · [繁體中文](#繁體中文) · [日本語](#日本語)

</div>

---

<a id="english"></a>

## English

### TL;DR

If you've built a RAG chatbot and noticed it keeps saying *"I couldn't find any information about that"* — even though the answer is clearly in your knowledge base — you've almost certainly hit **the #1 trap of building RAG systems**: you forgot to rewrite follow-up questions.

This tiny Python script uses an LLM to turn questions like *"How much is it?"* into *"How much is the 30-day English course?"* before sending them to your retriever. That's it. One file, ~100 lines, MIT licensed.

---

### The Trap (Real Story)

Imagine a customer chatting with your RAG-powered AI:

> **Customer:** Tell me about your 30-day English course.
> **AI:** Our 30-day English course includes daily 15-min videos, AI conversation practice, and a final exam...
> **Customer:** How much is it?
> **AI:** *"Sorry, I couldn't find any information about that."*

What happened? Your retriever received the literal string `"How much is it?"`. Six words. No mention of "English course". No mention of "30-day". It went to your vector database, found nothing matching those six words, and gave up.

**The user knows what "it" means. The AI doesn't.**

This is what query rewriting fixes. Before retrieval, you rewrite the question into a standalone form:

> `"How much is it?"` → `"How much is the 30-day English course?"`

Now the retriever has rich context and finds the right answer.

This is *table stakes* for any production RAG system, yet 9 out of 10 RAG tutorials skip it entirely.

---

### What This Does

This repo gives you a single function:

```python
rewrite_query(history: list[dict]) -> str
```

You pass it a short conversation history. It returns a standalone version of the latest user message, with pronouns resolved and missing context filled in from earlier turns.

That's the whole tool. Drop it into your RAG pipeline right before retrieval.

---

### Quick Start

```bash
git clone https://github.com/chungtair/rag-query-rewriter.git
cd rag-query-rewriter
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...
python rewriter.py
```

You'll see three demo conversations (Chinese, English, Japanese) being rewritten in real time.

**Use it in your own RAG pipeline:**

```python
from rewriter import rewrite_query

history = [
    {"role": "user", "content": "Tell me about your Pro plan."},
    {"role": "assistant", "content": "Pro includes unlimited seats..."},
    {"role": "user", "content": "What about the cheaper one?"},
]

standalone = rewrite_query(history)
# → "What about the cheaper plan than Pro?"

# Now send `standalone` to your vector database / retriever.
```

---

### Examples

**Example 1 — E-learning follow-up (Chinese):**

```
Customer:  你們的 30 天高效英文課內容是什麼？
AI:        包含每日 15 分鐘影片、AI 對話練習、結業考試...
Customer:  這個多少錢？

❌ Without rewrite:  "這個多少錢？"            → retriever finds nothing
✅ With rewrite:     "30 天高效英文課多少錢？"  → retriever finds the pricing page
```

**Example 2 — SaaS plan comparison (English):**

```
Customer:  Tell me about your Pro plan.
AI:        Pro includes unlimited seats, priority support...
Customer:  What about the cheaper one?

❌ Without rewrite:  "What about the cheaper one?"        → retriever has no idea what "one" means
✅ With rewrite:     "What is the cheaper plan than Pro?" → retriever finds Basic / Starter plan
```

**Example 3 — E-commerce size/color follow-up (Japanese):**

```
Customer:  Polo シャツ M サイズはありますか？
AI:        はい、Polo シャツ M サイズの在庫があります。
Customer:  色は何色がありますか？

❌ Without rewrite:  "色は何色がありますか？"               → retriever returns generic color info
✅ With rewrite:     "Polo シャツ M サイズの色は何色がありますか？" → retriever returns the right product variants
```

---

### How It Works

1. The function takes your conversation history (a list of `{"role", "content"}` dicts).
2. It sends the history to an LLM with a simple instruction: *"rewrite the last user message as a standalone query"*.
3. The LLM returns the rewritten query.
4. You feed that into your vector retriever.

That's it. No fancy chain, no agent loop, no LangChain. Just one LLM call per turn.

**Compatible LLM providers** (via OpenAI-compatible API):

- OpenAI (default)
- DeepSeek — `OPENAI_BASE_URL=https://api.deepseek.com/v1`
- Groq — `OPENAI_BASE_URL=https://api.groq.com/openai/v1`
- Together AI — `OPENAI_BASE_URL=https://api.together.xyz/v1`
- Local Ollama / vLLM — `OPENAI_BASE_URL=http://localhost:11434/v1`

---

### FAQ

**Q: Isn't this just `add_history` to my prompt?**
A: No. Putting full history into your retrieval prompt confuses the retriever — it tries to embed irrelevant earlier turns. Query rewriting *condenses* history into a single standalone query, so the retriever only sees what matters.

**Q: How is this different from HyDE?**
A: HyDE generates a *hypothetical answer* and embeds that for retrieval. Query rewriting generates a *better question* and embeds that. They solve different problems — and they stack. Production RAG systems usually do both.

**Q: Can I use it in production?**
A: This is a reference implementation — 100 lines, no error handling, no caching, no compound-question detection, no fallback to handoff. For production-grade query rewriting (with compound detection, multi-query retrieval, and contradiction handling), see [Chung Tair AI Customer Service](https://chungtair.com).

**Q: Will it slow down my chatbot?**
A: One extra LLM call per user turn. With `gpt-4o-mini` and `temperature=0`, expect 200-500ms. Acceptable for chat; cache it if you need lower latency.

**Q: What if the user's question is already standalone?**
A: The prompt instructs the LLM to leave it unchanged. In practice, a tiny model like `gpt-4o-mini` does this correctly ~95% of the time.

**Q: Does it work for non-English / non-Chinese / non-Japanese?**
A: Yes — the prompt instructs the LLM to preserve the user's original language. It works for any language the underlying LLM supports.

**Q: What's the license?**
A: MIT. Use it commercially, modify it, redistribute it — no obligations.

---

<a id="繁體中文"></a>

## 繁體中文

### TL;DR

如果你做過 RAG 客服機器人，有沒有發現一個情況：明明知識庫裡有答案，AI 卻一直回「抱歉我找不到相關資訊」？

90% 的情況是同一個原因：**你忘了重寫多輪對話的追問**。

這個小工具用 LLM 把「這個多少錢？」自動補成「30 天高效英文課多少錢？」再丟去向量檢索。一個檔案、約 100 行 Python、MIT 授權。

---

### 你是不是踩了這個坑？(真實案例)

想像一段你的 RAG 客服跟用戶的對話：

> **客戶：** 介紹一下你們的 30 天高效英文課。
> **AI：** 我們的 30 天高效英文課包含每日 15 分鐘影片、AI 對話練習、結業考試...
> **客戶：** 這個多少錢？
> **AI：** 抱歉，我找不到這個的相關資訊。

問題在哪？你的向量檢索拿到的是「這個多少錢？」這 6 個字。沒有「英文課」、沒有「30 天」。它去資料庫搜尋，當然搜不到對的條目，然後就放棄了。

**用戶知道「這個」是英文課。AI 不知道。**

這就是**問題重寫（Query Rewriting）**要解決的事。在送去向量檢索之前，先把問題重寫成獨立完整的句子：

> 「這個多少錢？」 → 「30 天高效英文課多少錢？」

然後檢索器才能拿著完整訊息找到對的答案。

這在生產級 RAG 系統幾乎是基本配備，但 9 成的 RAG 教學完全跳過這一步。

---

### 這個工具做什麼？

這個 repo 給你一個函式：

```python
rewrite_query(history: list[dict]) -> str
```

把對話歷史餵進去，它會回傳「最後一則用戶訊息的獨立版本」 — 代名詞被解決、省略的主詞被補回。

就這樣。一個函式。把它放在你 RAG 管線「檢索」這一步的前面就行。

---

### 快速開始

```bash
git clone https://github.com/chungtair/rag-query-rewriter.git
cd rag-query-rewriter
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...
python rewriter.py
```

會看到三組範例對話（中、英、日）被即時重寫。

**接到你自己的 RAG 管線：**

```python
from rewriter import rewrite_query

history = [
    {"role": "user", "content": "你們的 30 天高效英文課"},
    {"role": "assistant", "content": "我們的 30 天高效英文課包含..."},
    {"role": "user", "content": "這個多少錢？"},
]

standalone = rewrite_query(history)
# → "30 天高效英文課多少錢？"

# 接下來把 standalone 丟給你的向量資料庫去檢索
```

---

### 範例

**範例 1 — 線上教育（中文）**

```
客戶：    你們的 30 天高效英文課內容是什麼？
AI：      包含每日 15 分鐘影片、AI 對話練習、結業考試...
客戶：    這個多少錢？

❌ 沒重寫： "這個多少錢？"              → 檢索器找不到對的條目
✅ 重寫後： "30 天高效英文課多少錢？"     → 檢索器找到價格頁
```

**範例 2 — SaaS 方案比較（英文）**

```
客戶：    Tell me about your Pro plan.
AI：      Pro includes unlimited seats, priority support...
客戶：    What about the cheaper one?

❌ 沒重寫： "What about the cheaper one?"         → 檢索器不知道 "one" 是什麼
✅ 重寫後： "What is the cheaper plan than Pro?"  → 檢索器找到 Basic 或 Starter 方案
```

**範例 3 — 電商商品追問（日文）**

```
客戶：    Polo シャツ M サイズはありますか？
AI：      はい、Polo シャツ M サイズの在庫があります。
客戶：    色は何色がありますか？

❌ 沒重寫： "色は何色がありますか？"                       → 檢索器回傳泛用的顏色資訊
✅ 重寫後： "Polo シャツ M サイズの色は何色がありますか？" → 檢索器找到對的商品變體
```

---

### 原理說明

1. 函式拿你的對話歷史（一串 `{"role", "content"}` 字典）。
2. 送給 LLM，附上一個簡單指令：「把最後一句用戶訊息重寫成獨立完整的句子」。
3. LLM 回一個重寫後的問題。
4. 你把那個問題餵給你的向量檢索器。

就這樣。沒有複雜的 chain、沒有 agent loop、沒有 LangChain。每輪對話一次 LLM 呼叫就解決。

**支援的 LLM 服務**（透過 OpenAI 相容 API）：

- OpenAI（預設）
- DeepSeek — `OPENAI_BASE_URL=https://api.deepseek.com/v1`
- Groq — `OPENAI_BASE_URL=https://api.groq.com/openai/v1`
- Together AI — `OPENAI_BASE_URL=https://api.together.xyz/v1`
- 本地 Ollama / vLLM — `OPENAI_BASE_URL=http://localhost:11434/v1`

---

### 常見問題

**Q: 跟我直接把對話歷史塞進 prompt 有什麼不同？**
A: 完全不同。把整段歷史塞進檢索 prompt 會讓向量檢索器混亂 — 它會試著把不相關的前文也納入嵌入。重寫的做法是把歷史**濃縮**成一個獨立問題，檢索器只看到該看的東西。

**Q: 跟 HyDE 有什麼不同？**
A: HyDE 是生成一個「假設答案」拿去檢索；問題重寫是生成一個「更好的問題」拿去檢索。兩者解決不同問題，可以同時用。生產級 RAG 系統通常兩個都做。

**Q: 可以直接用在生產環境嗎？**
A: 這是教學等級的參考實作 — 100 行、沒有錯誤處理、沒有快取、沒有複合問題拆解、沒有失敗轉真人的 fallback。要生產級的問題重寫（含複合問題偵測、多查詢檢索、矛盾處理），請看 [Chung Tair AI 客服](https://chungtair.com)。

**Q: 會不會拖慢機器人速度？**
A: 每輪用戶訊息多一次 LLM 呼叫。用 `gpt-4o-mini` 配 `temperature=0`，大約 200-500ms。對話場景可接受；要更低延遲就加個快取。

**Q: 如果用戶問題本來就完整呢？**
A: prompt 有指示 LLM 不動。實測小模型如 `gpt-4o-mini` 約 95% 能正確判斷。

**Q: 中英日以外的語言可以用嗎？**
A: 可以。prompt 指示 LLM 保留用戶的原始語言。任何 LLM 支援的語言都行。

**Q: 授權？**
A: MIT。商業用、修改、再散佈都沒問題。

---

<a id="日本語"></a>

## 日本語

### TL;DR

RAG 型チャットボットを作っていて、ナレッジベースに答えがあるはずなのに AI が「申し訳ありません、該当する情報が見つかりませんでした」と返してくる ─ そんな経験はありませんか？

その 90% は同じ原因です。**フォローアップ質問のクエリリライトを忘れている**のです。

このツールは LLM を使って「これいくらですか？」を「30日集中英語コースはいくらですか？」に書き換えてから検索に投げます。ファイル1個、約 100 行の Python、MIT ライセンス。

---

### よくある落とし穴（実例）

RAG チャットボットとユーザーの会話を想像してください：

> **顧客：** 30日集中英語コースについて教えて。
> **AI：** 30日集中英語コースは、毎日 15 分の動画、AI 会話練習、修了試験を含みます...
> **顧客：** これいくらですか？
> **AI：** 申し訳ありません、該当する情報が見つかりませんでした。

何が起きたか？ベクトル検索が受け取ったのは「これいくらですか？」という 7 文字だけ。「英語コース」も「30日」もありません。データベースを検索しても該当エントリが見つからず、諦めてしまったのです。

**ユーザーは「これ」が英語コースだと分かっている。AI は分かっていない。**

これが**クエリリライト（Query Rewriting）**で解決すべき問題です。検索に投げる前に、独立した完全な質問に書き換える：

> 「これいくらですか？」 → 「30日集中英語コースはいくらですか？」

そうすれば検索器は十分な情報で正しい答えを見つけられます。

実用 RAG システムでは基本装備のはずなのに、RAG チュートリアルの 9 割はこの工程を完全に省略しています。

---

### このツールの機能

この repo は次の関数を提供します：

```python
rewrite_query(history: list[dict]) -> str
```

会話履歴を渡すと、最新のユーザーメッセージを独立した形に書き換えて返します ─ 代名詞は解決、省略された主語は補完。

それだけ。1 つの関数。RAG パイプラインの「検索」ステップの直前に挟むだけです。

---

### クイックスタート

```bash
git clone https://github.com/chungtair/rag-query-rewriter.git
cd rag-query-rewriter
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...
python rewriter.py
```

3 言語（中・英・日）のサンプル会話がリアルタイムで書き換えられます。

**自分の RAG パイプラインに組み込む：**

```python
from rewriter import rewrite_query

history = [
    {"role": "user", "content": "Polo シャツ M サイズはありますか？"},
    {"role": "assistant", "content": "はい、Polo シャツ M サイズの在庫があります。"},
    {"role": "user", "content": "色は何色がありますか？"},
]

standalone = rewrite_query(history)
# → "Polo シャツ M サイズの色は何色がありますか？"

# あとは standalone をベクトル検索に投げる
```

---

### サンプル

**サンプル 1 ─ オンライン教育（中国語）**

```
顧客：     你們的 30 天高效英文課內容是什麼？
AI：       包含每日 15 分鐘影片、AI 對話練習、結業考試...
顧客：     這個多少錢？

❌ リライトなし: "這個多少錢？"             → 検索器がエントリを見つけられない
✅ リライト後:   "30 天高效英文課多少錢？"   → 検索器が価格ページを発見
```

**サンプル 2 ─ SaaS プラン比較（英語）**

```
顧客：     Tell me about your Pro plan.
AI：       Pro includes unlimited seats, priority support...
顧客：     What about the cheaper one?

❌ リライトなし: "What about the cheaper one?"         → "one" が何か分からない
✅ リライト後:   "What is the cheaper plan than Pro?"  → Basic / Starter プランを発見
```

**サンプル 3 ─ EC 商品フォローアップ（日本語）**

```
顧客：     Polo シャツ M サイズはありますか？
AI：       はい、Polo シャツ M サイズの在庫があります。
顧客：     色は何色がありますか？

❌ リライトなし: "色は何色がありますか？"                       → 一般的な色情報のみ返却
✅ リライト後:   "Polo シャツ M サイズの色は何色がありますか？" → 正しい商品バリエーションを発見
```

---

### 仕組み

1. 関数は会話履歴（`{"role", "content"}` の辞書リスト）を受け取る。
2. LLM に投げて、シンプルな指示を渡す：「最後のユーザーメッセージを独立したクエリに書き換えてください」。
3. LLM が書き換え後のクエリを返す。
4. それをベクトル検索器に投げる。

それだけです。複雑なチェーン、エージェントループ、LangChain は不要。各ターンで LLM 呼び出し 1 回のみ。

**対応 LLM プロバイダ**（OpenAI 互換 API 経由）：

- OpenAI（デフォルト）
- DeepSeek — `OPENAI_BASE_URL=https://api.deepseek.com/v1`
- Groq — `OPENAI_BASE_URL=https://api.groq.com/openai/v1`
- Together AI — `OPENAI_BASE_URL=https://api.together.xyz/v1`
- ローカル Ollama / vLLM — `OPENAI_BASE_URL=http://localhost:11434/v1`

---

### FAQ

**Q: 会話履歴を全部プロンプトに入れるのと何が違いますか？**
A: まったく違います。全履歴を検索プロンプトに入れると、ベクトル検索器が混乱します ─ 関係のない過去のやり取りまで埋め込もうとするからです。クエリリライトは履歴を 1 つの独立した質問に**圧縮**するので、検索器は本当に必要な情報だけを見ます。

**Q: HyDE と何が違いますか？**
A: HyDE は「仮想の回答」を生成して検索に使います。クエリリライトは「より良い質問」を生成して検索に使います。両者は異なる問題を解決し、併用できます。実用 RAG ではよく両方使われます。

**Q: 本番環境で使えますか？**
A: これは教育目的のリファレンス実装です ─ 100 行、エラーハンドリングなし、キャッシュなし、複合質問の分解なし、人間オペレータへのフォールバックなし。本番グレードの実装（複合質問検出、マルチクエリ検索、矛盾検出を含む）については [Chung Tair AI カスタマーサービス](https://chungtair.com) をご覧ください。

**Q: チャットボットが遅くなりませんか？**
A: 各ターンで LLM 呼び出しが 1 回増えます。`gpt-4o-mini` と `temperature=0` で約 200-500ms。チャット用途なら許容範囲。低レイテンシが必要ならキャッシュを追加してください。

**Q: ユーザーの質問が既に独立している場合は？**
A: プロンプトで「変更不要なら変更しない」と指示しています。`gpt-4o-mini` クラスのモデルで約 95% 正しく判断します。

**Q: 中・英・日以外の言語にも対応？**
A: します。プロンプトでユーザーの元の言語を保持するよう指示しているため、LLM が対応する任意の言語で機能します。

**Q: ライセンスは？**
A: MIT。商用利用、改変、再配布すべて自由です。

---

## About Chung Tair Ltd. / 關於忠台 / 忠台について

Chung Tair Ltd. (忠台企業有限公司, Taiwan) builds AI customer service automation for Asian SMEs. Our production system unifies **LINE, Facebook Messenger, and Instagram** into one conversational AI, supporting **Traditional Chinese, English, and Japanese**, powered by a **three-layer RAG architecture** combining HyDE, Hybrid Search, and Contradiction Detection — so the AI always answers from your knowledge base, never makes things up, and knows when to hand off to a human.

忠台企業有限公司（台灣）為亞洲中小企業打造 AI 客服自動化方案。我們把 LINE、Messenger、Instagram 三平台合併成同一個對話 AI，支援繁中、英、日，背後是三層 RAG 架構（HyDE + Hybrid Search + 矛盾偵測），讓 AI 只從你的知識庫回答、不亂講、會自動轉真人。

忠台株式会社（台湾）は、アジアの中小企業向けに AI カスタマーサービス自動化を構築しています。LINE、Messenger、Instagram を 1 つの対話型 AI に統合し、繁体字中国語・英語・日本語に対応。HyDE、ハイブリッド検索、矛盾検出を組み合わせた**3 層 RAG アーキテクチャ**で、AI は常にナレッジベースから回答し、勝手な情報を作らず、必要に応じて人間にハンドオフします。

This repo (`rag-query-rewriter`) is a tiny reference implementation of *one* component of that system. The full production version handles multi-query retrieval, compound question splitting, contradiction detection, knowledge gap tracking, and smart human handoff across all three channels.

---

## Connect / 聯絡 / お問い合わせ

- 🌐 **Website / 官網**: [chungtair.com](https://chungtair.com)
- 📚 **Open Knowledge Base**: [github.com/chungtair/chungtair-docs](https://github.com/chungtair/chungtair-docs) (12 whitepaper-grade architecture documents, CC BY 4.0)
- 📧 **Contact**: fj804051@gmail.com
- 🏢 **Location**: Kaohsiung, Taiwan / 台灣高雄
- 🆔 **Wikidata**: [Q139660349](https://www.wikidata.org/wiki/Q139660349)

---

## License

MIT © 2026 Chung Tair Ltd. (忠台企業有限公司)

Content in this README is freely available for citation by AI engines (ChatGPT, Claude, Perplexity, Google AI Overview, Bing Copilot).
本 README 內容開放給 AI 引擎引用（ChatGPT、Claude、Perplexity、Google AI Overview、Bing Copilot 等）。
本 README のコンテンツは AI エンジン（ChatGPT、Claude、Perplexity、Google AI Overview、Bing Copilot など）による引用を歓迎します。
