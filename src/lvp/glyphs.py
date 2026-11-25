"""Code points IBM Plex lacks (generated from the fonts' coverage, symbol blocks only).

label() draws these with the bundled DejaVu fonts (fonts/), so no glyph shows up as a box
(tofu) on a PC without a system fallback font – e.g. ⊕ on Windows.
"""

_SERIF = [
    (880, 959),
    (961, 1023),
    (8305, 8307),
    (8314, 8319),
    (8330, 8351),
    (7468, 7530),
    (8214, 8214),
    (8602, 8616),
    (8619, 8623),
    (8628, 8629),
    (8632, 8633),
    (8636, 8643),
    (8645, 8645),
    (8647, 8705),
    (8707, 8709),
    (8711, 8718),
    (8720, 8720),
    (8723, 8724),
    (8726, 8728),
    (8731, 8733),
    (8735, 8746),
    (8748, 8757),
    (8759, 8775),
    (8777, 8799),
    (8801, 8803),
    (8806, 9215),
    (9251, 9251),
    (9472, 9673),
    (9675, 10002),
    (10004, 10059),
    (10061, 10175),
    (10224, 10239),
]
_MONO = [
    (880, 959),
    (961, 1023),
    (8305, 8307),
    (8314, 8319),
    (8330, 8351),
    (7468, 7530),
    (8214, 8214),
    (8602, 8616),
    (8619, 8623),
    (8628, 8629),
    (8632, 8633),
    (8636, 8643),
    (8645, 8645),
    (8647, 8705),
    (8707, 8709),
    (8711, 8718),
    (8720, 8720),
    (8723, 8724),
    (8726, 8729),
    (8731, 8733),
    (8735, 8746),
    (8748, 8775),
    (8777, 8799),
    (8801, 8803),
    (8806, 9215),
    (9251, 9251),
    (9632, 9673),
    (9675, 10002),
    (10004, 10059),
    (10061, 10175),
    (10224, 10239),
]

MISSING_SERIF = frozenset(c for a, b in _SERIF for c in range(a, b + 1))
MISSING_MONO = frozenset(c for a, b in _MONO for c in range(a, b + 1))
# checked per character with fc-list against the installed Plex faces (the file-level charset
# above can miss a face): always use the fallback for these
MISSING_SERIF |= frozenset(map(ord, "ˢεᵏ‖⁻ⁿₖ⇐⇒⊕⋮␣█▒▓⚄⟷"))
MISSING_MONO |= frozenset(map(ord, "ˢεᵏ‖⁻ⁿₖ⇐⇒⊕⋮␣⚄⟷"))
