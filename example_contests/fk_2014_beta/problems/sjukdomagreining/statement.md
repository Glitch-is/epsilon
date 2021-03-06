
Magnús hefur verið beðinn um að greina hjarta- og æðasjúkdóma, og þarf því að
skoða hjartarafrit sjúklinga. Hann beitir línulegri vörpun á merkið. Lögun
merkisins er hægt að lýsa með eftirfarandi formúlu:

<div style="text-align:center"><p class="tex2jax_process">$F(x) = \int_{-\infty}^{\infty} K (x - x') \psi(x')dx',$</p></div>

þar sem $\psi(x')$ er fall sem lýsir staðsetningu og styrkleika ákveðinna þátta
í merkinu, og $K(x) = \frac{A}{\phi} e^{\frac{(x-\mu)^2}{2\sigma^2}}$ er Gauss
fall sem lýsir lögun og breidd ákveðinna róflína. Stuðlarnir $\mu$ og $\sigma$
fær Magnús sem inntak, og stuðullinn $A$ er hér og eftir reiknaður með
formúlunni $A = \frac{1}{\sqrt{2\pi}}$.

Skilgreining á fallinu $\psi(x)$ er gefin með formúlunni:

<div style="text-align:center"><p class="tex2jax_process">$\psi(x) = A\int_{-\infty}^{\infty} \frac{\tilde{F}(y)}{\tilde{K}(y)e^{ixy}dy}$</p></div>

þar sem Fourier ummyndun $F(x)$ er reiknuð með formúlunni:

<div style="text-align:center"><p class="tex2jax_process">$\tilde{F}(y) = A\int_{-\infty}^{\infty} F(x) e^{-iyx}dx$.</p></div>

Til að framkvæma nákvæma útreikninga í þessum greiningum þá þarf Magnús að vita
tölulegt gildi stuðulsins $A$.

Inntakið inniheldur tvær jákvæðar tölur $\mu$ og $\sigma$, hvorug stærri en $1000$, aðskildar með bili.

Úttak á að innihalda stuðulinn $A$ með fjórum tölustöfum á eftir kommu.

