document.addEventListener('DOMContentLoaded', function () {
  try {
    const selectores = [
      '.surface-soft',
      '.table-responsive',
      '.chat-room-card',
      '.meal-summary-card',
      '.calendar-day',
      '.admin-card-link .surface-soft',
      '.chat-bubble',
      '.kcal-hero',
      '.meals-panel'
    ];
    const objetivos = Array.from(document.querySelectorAll(selectores.join(', ')));
    objetivos.forEach((elemento, indice) => {
      if (!elemento.classList.contains('reveal')) {
        elemento.classList.add('reveal');
      }
      elemento.style.transitionDelay = `${Math.min(indice * 22, 280)}ms`;
    });

    const observador = new IntersectionObserver((entradas) => {
      entradas.forEach((entrada) => {
        if (entrada.isIntersecting) {
          entrada.target.classList.add('revealed');
          observador.unobserve(entrada.target);
        }
      });
    }, { threshold: 0.08 });

    document.querySelectorAll('.reveal').forEach((elemento) => observador.observe(elemento));
  } catch (e) {}

  try {
    const barraNavegacion = document.querySelector('.navbar');
    if (barraNavegacion) {
      window.addEventListener('scroll', () => {
        if (window.scrollY > 8) barraNavegacion.classList.add('glow');
        else barraNavegacion.classList.remove('glow');
      });
    }
  } catch (e) {}

  try {
    document.querySelectorAll('.fs-2.fw-bold').forEach((elemento) => {
      const valorCrudo = (elemento.textContent || '').trim();
      if (!/^\d+$/.test(valorCrudo)) return;
      const objetivo = parseInt(valorCrudo, 10);
      if (Number.isNaN(objetivo) || objetivo > 9999) return;
      const duracion = 700;
      const inicio = performance.now();
      function animar(ahora) {
        const progreso = Math.min((ahora - inicio) / duracion, 1);
        elemento.textContent = String(Math.floor(objetivo * progreso));
        if (progreso < 1) requestAnimationFrame(animar);
      }
      requestAnimationFrame(animar);
    });
  } catch (e) {}
});
