"""
Sample sentences per language (local text + French translation).
Replace or extend this list for your dataset.
"""

SENTENCES = {
    "yemba": [
        {"text_local": "O Ziɛ́", "translation": "Bonjour"},
        {"text_local": "má shʉ’ɛ̄ né nu mɛ̄ katɛ́ má ", "translation": " bonjour monsieur, je viens pour mon dossier"},
        {"text_local": "ma nsia gni té sá", "translation": "Merci beaucoup"},
        {"text_local": "pè lekɔ", "translation": "Comment allez-vous ?"},
        {"text_local": "A si ndiŋ", "translation": "Je vais bien"},
        {"text_local": "tsà Meŋ tsutè ú", "translation": "Laisse-moi t'aider"},
        {"text_local": "ú ŋɔ̄?", "translation": "Où es-tu ?"},
        {"text_local": "Mà ŋ́gyā", "translation": "Je suis à la maison"},
        {"text_local": "mé ŋgɔɛ́", "translation": "Allons-y"},
        {"text_local": "ngà ŋue kɔ̄ mbu pɛ́ ", "translation": "Allons-y"},
        {"text_local": "Té sá", "translation": "Beaucoup"},
        {"text_local": "Ndem ", "translation": "Que Dieu te bénisse"},
        {"text_local": "Meŋ ā si ŋkon' le ngue katé ŋu' la'  ", "translation": "j'aimerai faire un acte de naissance  "},
        {"text_local": "Meŋ ā shʉ’ɛ̄ mpfɔk katé ŋu' la'", "translation": "* je viens retirer mon acte de naissance "},
        {"text_local": "pɛ́ ŋwɛ̄ me katé ", "translation": " avez vous les documents"},
    ],
    "douala": [
        {"text_local": "Mbolo", "translation": "Bonjour"},
        {"text_local": "Matondo", "translation": "Merci"},
        {"text_local": "Ongué?", "translation": "Comment ça va ?"},
        {"text_local": "Mamá wé", "translation": "Je vais bien"},
        {"text_local": "Na wuti ve?", "translation": "Où vas-tu ?"},
        {"text_local": "Na ndáp ve", "translation": "À la maison"},
        {"text_local": "Tó kende", "translation": "Allons-y"},
        {"text_local": "Pénga mingi", "translation": "Très bien"},
        {"text_local": "Na sala nini?", "translation": "Qu'est-ce que tu fais ?"},
        {"text_local": "Na sala mosala", "translation": "Je travaille"},
    ],
    "ewondo": [
        {"text_local": "Mbolo", "translation": "Bonjour"},
        {"text_local": "Abomo", "translation": "Merci"},
        {"text_local": "Yénge ve?", "translation": "Comment vas-tu ?"},
        {"text_local": "Mamá wé", "translation": "Je vais bien"},
        {"text_local": "O ve ve?", "translation": "Où vas-tu ?"},
        {"text_local": "Ve ndá ve", "translation": "À la maison"},
        {"text_local": "Tó kende", "translation": "Allons-y"},
        {"text_local": "Mingi", "translation": "Beaucoup"},
        {"text_local": "O sala nini?", "translation": "Que fais-tu ?"},
        {"text_local": "Ma sala mosala", "translation": "Je travaille"},
    ],
}

LANGUAGE_LABELS = {
    "yemba": "Yemba",
    "douala": "Douala",
    "ewondo": "Ewondo",
}
