document.addEventListener('DOMContentLoaded', function() {
    const endTimeElement = document.getElementById('end-time');
    if (endTimeElement) {
        const endTime = new Date(endTimeElement.dataset.endTime).getTime();
        const timerDisplay = document.getElementById('timer');

        function updateTimer() {
            const now = new Date().getTime();
            const timeLeft = endTime - now;

            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                timerDisplay.textContent = "Vaqt tugadi!";
                return;
            }

            const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
            timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        }

        const timerInterval = setInterval(updateTimer, 1000);
        updateTimer();
    }
});