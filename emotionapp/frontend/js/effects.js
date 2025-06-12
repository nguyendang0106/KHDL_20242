const EffectsModule = (() => {
    const canvas = document.getElementById('interactive-background');
    if (!canvas) {
        console.error("EffectsModule: Canvas #interactive-background not found.");
        return { init: () => {}, updateTheme: () => {} };
    }
    const ctx = canvas.getContext('2d');

    let particlesArray = [];
    let mouse = { x: null, y: null, radius: 120 }; // Slightly larger interaction radius
    let animationFrameId;
    let currentTheme = 'dark';
    let hue = Math.random() * 360; // Start with a random hue

    function getCanvasBackgroundColor() {
        // Ensure CSS variables are loaded and accessible
        const color = getComputedStyle(document.documentElement).getPropertyValue('--current-canvas-bg').trim();
        return color || (currentTheme === 'light' ? '#e9ecef' : '#0a0a10'); // Fallback
    }

    function setCanvasSize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    class Particle {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            this.originX = x;
            this.originY = y;
            this.size = Math.random() * 1.5 + 0.5; // Smaller, more numerous particles
            this.density = (Math.random() * 20) + 5;
            this.vx = (Math.random() - 0.5) * 0.2; // Slight initial drift
            this.vy = (Math.random() - 0.5) * 0.2;
            this.maxSpeed = 1.2;
            this.springFactor = 0.008;
            this.damping = 0.96;
            // Theme-dependent colors for particles
            this.baseHue = hue; // Use the global shifting hue
            this.isTrail = false;
            this.life = 0;
            this.maxLife = Math.random() * 60 + 40; // Trail particle lifetime
        }

        draw() {
            let particleColor;
            if (this.isTrail) {
                const trailAlpha = Math.max(0, 1 - this.life / this.maxLife);
                particleColor = currentTheme === 'light' ?
                    `hsla(${(this.baseHue + 30) % 360}, 90%, 65%, ${trailAlpha * 0.8})` : // Brighter trail for light
                    `hsla(${(this.baseHue + 210) % 360}, 100%, 75%, ${trailAlpha})`;    // Contrasting trail for dark
            } else {
                particleColor = currentTheme === 'light' ?
                    `hsla(${this.baseHue % 360}, 60%, 55%, 0.6)` : // Softer particles for light bg
                    `hsla(${(this.baseHue + 180) % 360}, 80%, 65%, 0.7)`; // Brighter particles for dark bg
            }
            ctx.fillStyle = particleColor;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }

        update() {
            // Mouse interaction
            if (mouse.x !== null) {
                let dx = this.x - mouse.x;
                let dy = this.y - mouse.y;
                let distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < mouse.radius && distance > 0) { // Added distance > 0 check
                    let forceDirectionX = dx / distance;
                    let forceDirectionY = dy / distance;
                    let force = (mouse.radius - distance) / mouse.radius * this.density * 0.15; // Stronger repel
                    this.vx += forceDirectionX * force;
                    this.vy += forceDirectionY * force;
                }
            }

            if (!this.isTrail) {
                // Spring back to origin
                let dxOrigin = this.originX - this.x;
                let dyOrigin = this.originY - this.y;
                this.vx += dxOrigin * this.springFactor;
                this.vy += dyOrigin * this.springFactor;
            }

            this.vx *= this.damping;
            this.vy *= this.damping;

            const currentSpeed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
            if (currentSpeed > this.maxSpeed) {
                this.vx = (this.vx / currentSpeed) * this.maxSpeed;
                this.vy = (this.vy / currentSpeed) * this.maxSpeed;
            }

            this.x += this.vx;
            this.y += this.vy;

            // Keep particles within bounds (optional, can push them back gently)
            if (!this.isTrail) {
                if (this.x < 0 || this.x > canvas.width) this.vx *= -0.5; // Bounce gently
                if (this.y < 0 || this.y > canvas.height) this.vy *= -0.5;
            }


            if (this.isTrail) {
                this.life++;
                this.size *= 0.95; // Trail fades faster
            }
        }
    }

    function initParticles() {
        particlesArray = [];
        const numberOfParticles = (canvas.width * canvas.height) / 10000; // Adjust for desired density
        for (let i = 0; i < numberOfParticles; i++) {
            let x = Math.random() * canvas.width;
            let y = Math.random() * canvas.height;
            particlesArray.push(new Particle(x, y));
        }
    }

    function createTrailParticle() {
        if (mouse.x !== null && mouse.y !== null) {
            for (let i = 0; i < 2; i++) { // Create a couple for a denser trail
                const trailParticle = new Particle(mouse.x + (Math.random()-0.5)*10, mouse.y + (Math.random()-0.5)*10);
                trailParticle.isTrail = true;
                trailParticle.size = Math.random() * 2.5 + 1;
                particlesArray.push(trailParticle);
            }
        }
    }

    function animate() {
        ctx.fillStyle = getCanvasBackgroundColor();
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        hue = (hue + 0.15) % 360; // Slower, subtle hue shift

        for (let i = 0; i < particlesArray.length; i++) {
            const p = particlesArray[i];
            p.baseHue = hue; // Update particle base hue for global shift
            p.update();
            p.draw();

            // Constellation effect
            if (!p.isTrail) {
                for (let j = i + 1; j < particlesArray.length; j++) {
                    const p2 = particlesArray[j];
                    if (!p2.isTrail) {
                        const dx = p.x - p2.x;
                        const dy = p.y - p2.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        const connectDistance = 100; // Connection distance
                        if (distance < connectDistance) {
                            ctx.beginPath();
                            const alpha = Math.max(0, (1 - distance / connectDistance) * 0.5);
                            ctx.strokeStyle = currentTheme === 'light' ? `rgba(50,50,50,${alpha})` : `rgba(200,200,255,${alpha})`;
                            ctx.lineWidth = 0.4;
                            ctx.moveTo(p.x, p.y);
                            ctx.lineTo(p2.x, p2.y);
                            ctx.stroke();
                        }
                    }
                }
            }

            if (p.isTrail && (p.life >= p.maxLife || p.size < 0.1)) {
                particlesArray.splice(i, 1);
                i--;
            }
        }
        animationFrameId = requestAnimationFrame(animate);
    }

    function handleMouseMove(event) {
        mouse.x = event.clientX;
        mouse.y = event.clientY;
        createTrailParticle();
    }

    function handleMouseOut() {
        mouse.x = null;
        mouse.y = null;
    }

    function updateTheme(newTheme) {
        currentTheme = newTheme;
    }

    function init() {
        setCanvasSize();
        initParticles();

        window.addEventListener('resize', () => {
            setCanvasSize();
            initParticles();
        });
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseout', handleMouseOut);

        if (animationFrameId) cancelAnimationFrame(animationFrameId);
        animate();
    }

    return {
        init: init,
        updateTheme: updateTheme
    };
})();
// Note: EffectsModule.init() is called from main.js inside DOMContentLoaded