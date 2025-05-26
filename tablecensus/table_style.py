BASE   = "font-family:'IBM Plex Sans';font-size:13pt"
HEADER = BASE + ";font-weight:bold"
GRAY   = "background-color:#f3f3f3"


def zebra(s, color="#f3f3f3"):
    # grey 2 ≈ Excel “Gray 2” = #d9d9d9
    return [
        f'background-color:{color}' if ((i % 2) == 0) else '' 
        for i in range(len(s))
    ]


def apply_d3_style(df):
    return (
        df.style
        .set_properties(
            **{
                "font-family": "IBM Plex Sans",   # Excel falls back if font not installed
                "font-size":   "13pt",
            }
        )
        .apply(zebra)                 # alternating row shade
        .apply_index(lambda s: [HEADER]*len(s), axis="columns")  # column headers
        .apply_index(lambda s: [BASE]*len(s),   axis="index")    # row index cells
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [("font-weight", "bold"), ("border", "1px solid black")]
                }
            ]
        )
    )

