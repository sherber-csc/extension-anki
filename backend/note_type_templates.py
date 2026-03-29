from __future__ import annotations

NOTE_TYPE_CSS = """
.card {
  font-family: Arial, sans-serif;
  font-size: 18px;
  text-align: left;
  color: #555555;
  background: white;
}

.sherber-front {
  text-align: center;
  font-family: Arial, sans-serif;
  padding: 28px 20px 20px;
}

.sherber-front .emoji {
  font-size: 60px;
  margin-bottom: 12px;
}

.sherber-front .word {
  font-size: 50px;
  color: #ff66b2;
  margin-bottom: 12px;
  font-weight: bold;
}

.sherber-front .audio {
  margin-bottom: 16px;
}

.sherber-front .ipa {
  font-size: 30px;
  color: #777777;
  margin-bottom: 30px;
}

.sherber-front .image-prompt {
  font-size: 16px;
  color: #555555;
  font-style: italic;
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  padding: 10px 18px;
  border-radius: 8px;
  display: inline-block;
  line-height: 1.45;
  max-width: 760px;
  margin-top: 18px;
}

.sherber-back {
  text-align: left;
  font-family: Arial, sans-serif;
  padding: 24px 30px;
  color: #555555;
}

.sherber-back .section {
  margin-bottom: 30px;
}

.sherber-back .section-title {
  font-weight: bold;
  font-size: 22px;
  padding-bottom: 5px;
  margin-bottom: 15px;
  border-bottom-width: 2px;
  border-bottom-style: solid;
}

.sherber-back .section-title.meaning {
  color: #ff66b2;
  border-bottom-color: #ff66b2;
}

.sherber-back .section-title.pair {
  color: #00cccc;
  border-bottom-color: #00cccc;
}

.sherber-back .section-title.example {
  color: #66b3ff;
  border-bottom-color: #66b3ff;
}

.sherber-back .meanings {
  color: #666666;
  font-size: 18px;
}

.sherber-back .meaning-item {
  line-height: 1.6;
  margin-bottom: 10px;
}

.sherber-back .meaning-pos {
  color: #ff9933;
  font-weight: bold;
}

.sherber-back .meaning-text {
  color: #666666;
  font-size: 18px;
}

.sherber-back .forms-inline {
  color: #999999;
  font-size: 15px;
  margin: -10px 0 26px 0;
  line-height: 1.5;
}

.sherber-back .forms-label,
.sherber-back .forms-value {
  color: #999999;
  font-size: 15px;
}

.sherber-back .pair-list,
.sherber-back .example-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
}

.sherber-back .pair-item,
.sherber-back .example-item {
  line-height: 1.55;
  margin-bottom: 12px;
}

.sherber-back .pair-item {
  color: #555555;
}

.sherber-back .pair-en {
  color: #00cccc;
  font-size: 18px;
}

.sherber-back .pair-zh {
  color: #999999;
  font-size: 16px;
}

.sherber-back .example-item {
  color: #666666;
  font-size: 18px;
  line-height: 1.4;
}

.sherber-back .example-sentence {
  color: #666666;
}

.sherber-back .example-meta {
  color: #7a7a7a;
  font-size: 17px;
}
""".strip()


CARD_TEMPLATES = [
    {
        "Name": "Card 1",
        "Front": """
<div class="sherber-front">
  <div class="emoji">{{emoji}}</div>
  <div class="word">{{word}}</div>
  {{#audio}}<div class="audio">[sound:{{audio}}]</div>{{/audio}}
  <div class="ipa">{{ipa}}</div>
  <div class="image-prompt">💡 Imagine: {{image_prompt}}</div>
</div>
""".strip(),
        "Back": """
<div class="sherber-back">
  <div class="section">
    <div class="section-title meaning">📖 Meaning</div>
    <div class="meanings">{{meanings}}</div>
  </div>
  <div class="section">
    <div class="section-title pair">🔗 Pair</div>
    <ul class="pair-list">{{pairs}}</ul>
  </div>
  <div class="section">
    <div class="section-title example">✍️ Example</div>
    <ul class="example-list">{{examples}}</ul>
  </div>
</div>
""".strip(),
    }
]
