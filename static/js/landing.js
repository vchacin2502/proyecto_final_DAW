document.addEventListener('DOMContentLoaded', function() {
    const botonTema = document.getElementById('themeToggle');
    const cuerpo = document.body;
    const temaGuardado = localStorage.getItem('cafit-theme');
    const prefiereOscuro = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (temaGuardado === 'dark' || (!temaGuardado && prefiereOscuro)) {
        cuerpo.classList.add('dark-theme');
        actualizarIconoTema('sun');
    } else {
        actualizarIconoTema('moon');
    }

    botonTema.addEventListener('click', alternarTema);

    function alternarTema() {
        cuerpo.classList.toggle('dark-theme');

        if (cuerpo.classList.contains('dark-theme')) {
            localStorage.setItem('cafit-theme', 'dark');
            actualizarIconoTema('sun');
        } else {
            localStorage.setItem('cafit-theme', 'light');
            actualizarIconoTema('moon');
        }
    }

    function actualizarIconoTema(icono) {
        if (!botonTema) return;
        if (icono === 'sun') {
            botonTema.innerHTML = '<i class="bi bi-sun-fill" aria-hidden="true"></i>';
        } else {
            botonTema.innerHTML = '<i class="bi bi-moon-fill" aria-hidden="true"></i>';
        }
    }

    document.querySelectorAll('a[href^="#"]').forEach(ancla => {
        ancla.addEventListener('click', function (evento) {
            const destino = this.getAttribute('href');
            if (destino !== '#') {
                evento.preventDefault();
                const elemento = document.querySelector(destino);
                if (elemento) {
                    elemento.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    const opcionesObservador = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observador = new IntersectionObserver(function(entradas) {
        entradas.forEach(entrada => {
            if (entrada.isIntersecting) {
                entrada.target.style.opacity = '1';
                entrada.target.style.transform = 'translateY(0)';
            }
        });
    }, opcionesObservador);
    
    document.querySelectorAll('.feature-card').forEach(tarjeta => {
        tarjeta.style.opacity = '0';
        tarjeta.style.transform = 'translateY(20px)';
        observador.observe(tarjeta);
    });

    document.querySelectorAll('.feature-card').forEach(tarjeta => {
        tarjeta.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        tarjeta.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    const enlacesNavegacion = document.querySelectorAll('.nav a[href^="#"]');
    const secciones = document.querySelectorAll('section[id]');
    
    window.addEventListener('scroll', () => {
        let seccionActual = '';
        
        secciones.forEach(seccion => {
            const parteSuperior = seccion.offsetTop;
            const alturaSeccion = seccion.clientHeight;
            
            if (pageYOffset >= parteSuperior - 200) {
                seccionActual = seccion.getAttribute('id');
            }
        });
        
        enlacesNavegacion.forEach(enlace => {
            enlace.style.color = 'var(--text-primary)';
            if (enlace.getAttribute('href') === `#${seccionActual}`) {
                enlace.style.color = 'var(--primary)';
            }
        });
    });
    
    window.addEventListener('load', () => {
        const contenidoHero = document.querySelector('.hero-content');
        const imagenHero = document.querySelector('.hero-image');
        
        if (contenidoHero) {
            contenidoHero.style.animation = 'slideInUp 0.8s ease-out';
        }
        
        if (imagenHero) {
            imagenHero.style.animation = 'slideInUp 0.8s ease-out 0.2s both';
        }
    });
});

