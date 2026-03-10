(function () {
    // Determina la base URL dinámicamente según donde esté alojado el script.
    // Ej: Si la web incluye <script src="https://mibackend.com/static/widget.js"></script>
    // backendBaseUrl será "https://mibackend.com"
    const scriptTag = document.currentScript;
    const scriptUrl = new URL(scriptTag.src);
    const backendBaseUrl = scriptUrl.origin;

    // Inyectar el CSS de forma dinámica
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = `${backendBaseUrl}/static/widget.css`;
    document.head.appendChild(link);

    // Parseador Markdown muy básico (bold, lists y saltos de línea)
    function parseMarkdown(text) {
        let html = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br/>');
        return `<p>${html}</p>`;
    }

    // Estructura HTML del Widget
    const widgetHTML = `
        <div id="hta-widget-container">
            <div id="hta-chat-window">
                <div id="hta-chat-header">
                    <span style="display: flex; align-items: center; gap: 10px;">
                        <img src="https://www.hoteltresanclas.com/images/tresanclas/logo-hotel-tres-anclas-gandia.svg" alt="Logo Hotel Tres Anclas" style="height: 30px; filter: brightness(0) invert(1);">
                    </span>
                    <button id="hta-close-btn" aria-label="Cerrar chat">
                        <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"></path></svg>
                    </button>
                </div>
                
                <!-- Pantalla RGPD Inicial -->
                <div id="hta-rgpd-screen">
                    <h3>Tu Asistente Virtual</h3>
                    <p>Estoy aquí para resolver tus dudas de forma instantánea. Antes de comenzar, por favor acepta nuestra política de datos.</p>
                    <div class="hta-rgpd-checkbox-wrapper">
                        <input type="checkbox" id="hta-rgpd-checkbox">
                        <label for="hta-rgpd-checkbox">He leído y acepto el tratamiento de datos y privacidad para consultas comerciales mediante este chat.</label>
                    </div>
                    <button id="hta-rgpd-accept-btn" disabled>Comenzar la conversación</button>
                </div>

                <div id="hta-chat-messages">
                    <div class="hta-message hta-bot">
                        <p>¡Hola! Soy el asistente virtual del Hotel Tres Anclas. ✨ ¿En qué puedo ayudarte a preparar tu estancia?</p>
                    </div>
                </div>
                
                <div id="hta-chat-input-area">
                    <div id="hta-suggestions-chips"></div>
                    <div style="display: flex; gap: 12px; width: 100%;">
                        <input type="text" id="hta-chat-input" placeholder="Escribe tu consulta..." autocomplete="off" disabled>
                        <button id="hta-send-btn" disabled>
                            <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path></svg>
                        </button>
                    </div>
                </div>
            </div>
            
            <button id="hta-widget-button" aria-label="Abrir asistente virtual">
                <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"></path></svg>
            </button>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', widgetHTML);

    // Referencias a los elementos inyectados en el DOM
    const widgetContainer = document.getElementById('hta-widget-container');
    const chatWindow = document.getElementById('hta-chat-window');
    const widgetButton = document.getElementById('hta-widget-button');
    const closeBtn = document.getElementById('hta-close-btn');
    const inputField = document.getElementById('hta-chat-input');
    const sendBtn = document.getElementById('hta-send-btn');
    const messagesContainer = document.getElementById('hta-chat-messages');
    const suggestionsContainer = document.getElementById('hta-suggestions-chips');

    // Referencias elementos RGPD
    const rgpdScreen = document.getElementById('hta-rgpd-screen');
    const rgpdCheckbox = document.getElementById('hta-rgpd-checkbox');
    const rgpdAcceptBtn = document.getElementById('hta-rgpd-accept-btn');

    let isRgpdAccepted = false;
    let chatHistory = [];
    
    // Obtener o crear un ID de sesión para estadísticas
    let sessionId = localStorage.getItem('hta_session_id');
    if (!sessionId) {
        sessionId = 'sess_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        localStorage.setItem('hta_session_id', sessionId);
    }

    // Lógica de apertura/cierre del chat
    function toggleChat() {
        chatWindow.classList.toggle('hta-open');
        if (chatWindow.classList.contains('hta-open') && isRgpdAccepted) {
            inputField.focus();
        }
    }

    widgetButton.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', () => chatWindow.classList.remove('hta-open'));

    // Lógica validación RGPD
    rgpdCheckbox.addEventListener('change', (e) => {
        rgpdAcceptBtn.disabled = !e.target.checked;
    });

    rgpdAcceptBtn.addEventListener('click', () => {
        isRgpdAccepted = true;
        rgpdScreen.style.opacity = '0';
        setTimeout(() => {
            rgpdScreen.style.display = 'none';
            inputField.disabled = false;
            sendBtn.disabled = false;
            inputField.focus();
            showSuggestions();
        }, 300);
    });

    // Sugerencias proactivas
    function showSuggestions() {
        const suggestions = [
            { text: "📍 Ubicación", query: "¿Dónde está el hotel y cómo llegar?" },
            { text: "⏰ Horarios", query: "¿Cuáles son los horarios de entrada, salida y comidas?" },
            { text: "🏊 Servicios", query: "¿Qué servicios e instalaciones tiene el hotel?" },
            { text: "💳 Reservar", query: "¿Cómo puedo hacer una reserva?" }
        ];

        suggestionsContainer.innerHTML = '';
        suggestions.forEach(s => {
            const chip = document.createElement('button');
            chip.className = 'hta-suggestion-chip';
            chip.textContent = s.text;
            chip.onclick = () => {
                inputField.value = s.query;
                sendMessage();
                suggestionsContainer.style.display = 'none';
            };
            suggestionsContainer.appendChild(chip);
        });
        suggestionsContainer.style.display = 'flex';
    }

    // Añadir mensaje a la interfaz
    function appendMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `hta-message hta-${sender}`;

        if (sender === 'bot') {
            msgDiv.innerHTML = parseMarkdown(text);
        } else {
            msgDiv.textContent = text;
        }

        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    // Centrar vista al final del contenedor de mensajes
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Indicador de "Escribiendo..."
    function showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'hta-message hta-bot hta-typing-indicator';
        typingDiv.id = 'hta-typing';
        typingDiv.innerHTML = '<div class="hta-typing-dot"></div><div class="hta-typing-dot"></div><div class="hta-typing-dot"></div>';
        messagesContainer.appendChild(typingDiv);
        scrollToBottom();
    }

    function hideTyping() {
        const typingDiv = document.getElementById('hta-typing');
        if (typingDiv) {
            typingDiv.remove();
        }
    }

    // Encapsulamiento del envío asíncrono
    async function sendMessage() {
        const text = inputField.value.trim();
        if (!text) return;

        inputField.value = '';
        inputField.disabled = true;
        sendBtn.disabled = true;

        appendMessage(text, 'user');
        chatHistory.push({ role: 'user', content: text });

        showTyping();

        try {
            const response = await fetch(`${backendBaseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    messages: chatHistory,
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error('Error en el backend o red');
            }

            const data = await response.json();
            hideTyping();

            appendMessage(data.reply, 'bot');
            chatHistory.push({ role: 'model', content: data.reply });

        } catch (error) {
            hideTyping();
            console.error('Error al conectar con la API Asistente IA:', error);
            appendMessage('Lo siento, estoy teniendo problemas técnicos de conexión. Inténtalo de nuevo en unos momentos o llama a Recepción.', 'bot');

            // Revertir el estado del último mensaje enviado por el usuario para no desbalancear el historial
            chatHistory.pop();
        } finally {
            inputField.disabled = false;
            sendBtn.disabled = false;
            inputField.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

})();
