// DOM Elements
const micBtn = document.getElementById('micBtn');
const messagesContainer = document.getElementById('messagesContainer');
const messagesSection = document.getElementById('messagesSection');
const voiceStatus = document.getElementById('voiceStatus');
const waveform = document.getElementById('waveform');

// Speech Recognition Setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.continuous = false;
recognition.interimResults = true;
recognition.lang = 'en-US';

// Speech Synthesis
const synth = window.speechSynthesis;

let isListening = false;

// Speech Recognition Events
recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add('listening');
    waveform.classList.add('active');
    voiceStatus.textContent = 'Listening...';
    messagesSection.classList.add('active');
};

recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove('listening');
    waveform.classList.remove('active');
    voiceStatus.textContent = 'Ready to listen';
};

recognition.onresult = (event) => {
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
        }
    }

    if (finalTranscript) {
        voiceStatus.textContent = 'Processing...';
        sendMessage(finalTranscript.trim());
    }
};

recognition.onerror = (event) => {
    console.error('Speech recognition error', event.error);
    voiceStatus.textContent = 'Error listening. Try again.';
    micBtn.classList.remove('listening');
    waveform.classList.remove('active');
    isListening = false;
};

// Toggle Voice Recognition
function toggleVoiceRecognition() {
    if (isListening) {
        recognition.stop();
    } else {
        voiceStatus.textContent = 'Listening...';
        recognition.start();
    }
}

// Speak Text (AI Response)
function speakText(text) {
    // Cancel any ongoing speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    synth.speak(utterance);
}

// Send Message
function sendMessage(message) {
    if (message === '') return;

    // Add user message to chat
    addMessage(message, 'user');

    // Simulate AI response
    setTimeout(() => {
        const responses = [
            'That\'s a great question! Let me help you with that.',
            'I understand. Here\'s what I think about that...',
            'Interesting! I can assist you with that.',
            'Got it! Let me provide some information...',
            'That\'s helpful context. I\'ll help you out!',
            'I see what you mean. Let me explain...',
            'Great! That\'s very helpful information.'
        ];
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        addMessage(randomResponse, 'ai');
        voiceStatus.textContent = 'Ready to listen';
        
        // Speak the AI response
        speakText(randomResponse);
    }, 500);
}

// Add Message to Chat
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;

    messageDiv.appendChild(textDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Event Listeners
micBtn.addEventListener('click', toggleVoiceRecognition);
