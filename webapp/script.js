// Counter App JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const counterDisplay = document.getElementById('counter');
    const incrementBtn = document.getElementById('increment');
    const decrementBtn = document.getElementById('decrement');
    const resetBtn = document.getElementById('reset');
    
    let count = 0;
    
    function updateDisplay() {
        counterDisplay.textContent = count;
    }
    
    incrementBtn.addEventListener('click', () => {
        count++;
        updateDisplay();
    });
    
    decrementBtn.addEventListener('click', () => {
        count--;
        updateDisplay();
    });
    
    resetBtn.addEventListener('click', () => {
        count = 0;
        updateDisplay();
    });
});
