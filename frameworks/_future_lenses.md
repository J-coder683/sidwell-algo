# Future lenses — placeholders for build phases 4+

These are stubs for the build agent. Do not implement yet. v0.5 ships the Buffett, Marks, KKR, Blackstone, and Apollo lenses. These are documented here so the agent leaves matching stub files in `lenses/` with NotImplementedError raises.

## Implemented Lenses
- Buffett (v0.1)
- Marks (v0.3)
- KKR (v0.5)
- Blackstone (v0.5)
- Apollo (v0.5)

## Distressed lens (phase 6)
Special situations / distressed debt or equity.
Tests: trading below liquidation value, capital structure breakable, catalyst visible, recovery scenario asymmetric.
Sources: Marks memos on distressed; Moyer "Distressed Debt Analysis"; Gilson "Creating Value Through Corporate Restructuring".
