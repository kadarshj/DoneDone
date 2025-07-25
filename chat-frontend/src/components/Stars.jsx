import { useEffect } from 'react';

function Stars() {

    // Generate star field
    const generateStars = () => {
        const starsContainer = document.getElementById('stars');
        if (!starsContainer) { // Important: Check if the element exists
            return;
        }
        const numStars = 100;

        // Clear existing stars to prevent duplicates on re-renders
        starsContainer.innerHTML = '';

        for (let i = 0; i < numStars; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.width = star.style.height = Math.random() * 3 + 1 + 'px';
            star.style.animationDelay = Math.random() * 2 + 's';
            star.style.animationDuration = (Math.random() * 3 + 1) + 's';
            starsContainer.appendChild(star);
        }
    };

    // Use useEffect to call generateStars after the component mounts
    useEffect(() => {
        generateStars();
    }, []);

    return (
        <div className="stars" id="stars"></div>
    )
}

export default Stars