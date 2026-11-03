"""Other ways to say a lexicon's phrases. Applied to every scene's lexicon (worlds.LEXICON) by `apply()`: where a
lexicon says a change, a state, a frame or a want with one of these phrases, it gets the alternatives too, and the
printer takes them in turn from each story's seed. Every alternative is admitted only if the reader recovers the
same shape in a sentence (tools/probe_variants.py checks them all)."""

FLIPS = {
    "gave way": ["gave way", "came free", "slid free"],
    "snapped back into place": ["snapped back into place", "clicked back into place"],
    "sprang open": ["sprang open", "flew open", "popped open"],
    "uncoiled": ["uncoiled", "sprang loose"],
    "flew out": ["flew out", "shot out"],
    "landed on the floor": ["landed on the floor", "dropped onto the floor"],
    "swung": ["swung", "fluttered"],
    "hung still again": ["hung still again", "fell still again"],
    "slid toward the shed": ["slid toward the shed", "scraped toward the shed"],
    "began to swing": ["began to swing", "started to flap"],
    "clicked into place": ["clicked into place", "slid into place"],
    "came loose": ["came loose", "slipped out"],
    "went down": ["went down", "sank in"],
    "sprang back": ["sprang back", "popped back up"],
    "lit up": ["lit up", "glowed"],
    "clicked open": ["clicked open", "snapped open"],
    "swung open": ["swung open", "creaked open"],
    "rang": ["rang", "rang loudly"],
    "rang out": ["rang out", "sang out"],
    "slid across the floor": ["slid across the floor", "skidded across the floor"],
    "slid along the bench": ["slid along the bench", "skidded along the bench"],
    "flew off the path": ["flew off the path", "shot off the path"],
    "flew over the fence": ["flew over the fence", "sailed over the fence"],
    "came away": ["came away", "fell away"],
    "toppled": ["toppled", "toppled over"],
}

STATES = {
    "was shut tight": ["was shut tight", "was firmly closed"],
    "kept it shut": ["kept it shut", "held it fast"],
    "hung still": ["hung still", "hung limp"],
    "was locked": ["was locked", "was locked fast"],
    "hung loose": ["hung loose", "dangled free"],
    "sat by the gate": ["sat by the gate", "stood by the gate"],
    "was wound tight": ["was wound tight", "was coiled tight"],
}

FRAMES = {
    "There was a small wooden box on the table.": ["There was a small wooden box on the table.",
                                                   "A small wooden box sat on the table.",
                                                   "On the table stood a small wooden box."],
    "It was a windy afternoon in the yard.": ["It was a windy afternoon in the yard.",
                                              "The wind blew hard across the yard that afternoon."],
    "There was an old shed at the end of the garden.": ["There was an old shed at the end of the garden.",
                                                        "An old shed stood at the end of the garden."],
    "There was an old lamp on the workbench.": ["There was an old lamp on the workbench.",
                                                "An old lamp sat on the workbench."],
    "There was a wooden chest under the window.": ["There was a wooden chest under the window.",
                                                   "A wooden chest stood under the window."],
    "There was an old tin on the shelf.": ["There was an old tin on the shelf.", "An old tin sat on the shelf."],
    "There was a toy cannon on the rug.": ["There was a toy cannon on the rug.", "A toy cannon sat on the rug."],
    "There was an old catapult in the yard.": ["There was an old catapult in the yard.",
                                               "An old catapult stood in the yard."],
    "There was an old doorbell by the front door.": ["There was an old doorbell by the front door.",
                                                     "An old doorbell hung by the front door."],
}

WANTS = {   # "wanted to" reads as narrating; "longed to" and "set out to" as explaining(means, purpose) (printer)
    "wanted to open the box": ["wanted to open the box", "longed to open the box", "set out to open the box"],
    "wanted to open the cupboard": ["wanted to open the cupboard", "set out to open the cupboard"],
    "wanted to open the shed": ["wanted to open the shed", "longed to get into the shed"],
    "wanted to move the crate to the shed": ["wanted to move the crate to the shed",
                                             "set out to get the crate to the shed"],
    "wanted to open the chest": ["wanted to open the chest", "longed to open the chest"],
    "wanted to open the tin": ["wanted to open the tin", "set out to open the tin"],
    "wanted to ring the bell": ["wanted to ring the bell", "set out to ring the bell"],
    "wanted to fire the cannon": ["wanted to fire the cannon", "longed to fire the cannon"],
}


def _vary(value, table):
    if isinstance(value, str) and value in table:
        return list(table[value])
    return value


def apply(lexicons):
    """Give every lexicon the alternatives of the phrases it uses (in place; a lexicon whose entry is already
    several phrasings is left as it is)."""
    for lex in lexicons.values():
        if not lex:
            continue
        for key, table in (("flips", FLIPS), ("states", STATES), ("want", WANTS)):
            if isinstance(lex.get(key), dict):
                lex[key] = {k: _vary(v, table) for k, v in lex[key].items()}
        if "flips_obj" in lex:
            lex["flips_obj"] = {k: _vary(v, FLIPS) for k, v in lex["flips_obj"].items()}
        if isinstance(lex.get("frame"), str):
            lex["frame"] = _vary(lex["frame"], FRAMES)
        if isinstance(lex.get("frames"), dict):
            lex["frames"] = {k: _vary(v, FRAMES) for k, v in lex["frames"].items()}
