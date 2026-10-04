/*
 * Carrossel de produtos - /static/carrossel.js (T-0013; mesmo comportamento da T-0011).
 * Melhoria opcional: sem JS o carrossel rola com mouse, teclado e toque, e os botoes ficam escondidos.
 * Carregar com <script src="/static/carrossel.js" defer></script>. Sem codigo inline (CSP script-src 'self').
 */
(function () {
  "use strict";
  var reduzir = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll("[data-carrossel]").forEach(function (raiz) {
    var trilho = raiz.querySelector(".carrossel");
    var nav = raiz.querySelector(".carrossel-nav");
    if (!trilho || !nav) return;
    var anterior = nav.querySelector("[data-anterior]");
    var proximo = nav.querySelector("[data-proximo]");
    if (!anterior || !proximo) return;
    function passo() {
      var cartao = trilho.querySelector(".cartao");
      var gap = parseFloat(getComputedStyle(trilho.firstElementChild).columnGap) || 0;
      return cartao ? cartao.getBoundingClientRect().width + gap : trilho.clientWidth;
    }
    function atualizar() {
      var temMais = trilho.scrollWidth > trilho.clientWidth + 1;
      nav.hidden = !temMais;
      anterior.disabled = trilho.scrollLeft <= 1;
      proximo.disabled = trilho.scrollLeft + trilho.clientWidth >= trilho.scrollWidth - 1;
    }
    anterior.addEventListener("click", function () { trilho.scrollBy({ left: -passo(), behavior: reduzir ? "auto" : "smooth" }); });
    proximo.addEventListener("click", function () { trilho.scrollBy({ left: passo(), behavior: reduzir ? "auto" : "smooth" }); });
    trilho.addEventListener("scroll", atualizar, { passive: true });
    window.addEventListener("resize", atualizar);
    atualizar();
  });
})();
