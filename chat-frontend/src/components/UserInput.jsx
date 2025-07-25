import { useState, useEffect } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

function UserInput() {

    const [message, setMessage] = useState();
    const [isListening, setIsListening] = useState(false);
    const {
        transcript,
        listening,
        resetTranscript,
        browserSupportsSpeechRecognition
    } = useSpeechRecognition();

    function toggleListening(e) {
        if (isListening) {
            SpeechRecognition.stopListening();
            setIsListening(false);
        } else {
            SpeechRecognition.startListening({ continuous: true });
            setIsListening(true);
        }
    }

    function handleChange(e) {
        if (!isListening) {
            setMessage(e.target.value);
        }
    }

    useEffect(() => {
        if (isListening && transcript) {
            setMessage(transcript);
        }
    }, [transcript, isListening]);

    return (
        <div className="chat-container">
            {browserSupportsSpeechRecognition && (
                <button 
                className={`voice-command-btn ${isListening ? 'listening' : ''}`}
                onClick={toggleListening}>
                    🎤 {isListening ? 'STOP' : 'START'} VOICE COMMAND 
                </button>
            )}
            {!browserSupportsSpeechRecognition && (
                <span className="voice-command-btn"> Browser does not support speech recognition. </span>
            )}
            <textarea
            placeholder= {isListening ? "Listening..." : "Type your command or question..."}
            value={isListening ? transcript : message}
            onChange={handleChange}
            disabled={isListening}
            />
            <button className="process-btn">
                ⚡ INITIATE GALACTIC PROTOCOL ⚡
            </button>
        </div>
    )
}

export default UserInput;