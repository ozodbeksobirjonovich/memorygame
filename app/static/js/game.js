// app/static/js/game.js
document.addEventListener('DOMContentLoaded', function () {

    // O'yin elementlari
    const elements = {
        gameContainer: document.getElementById('game-container'),
        startButton: document.getElementById('start-button'),
        restartButton: document.getElementById('restart-button'),
        continueButton: document.getElementById('continue-button'),
        useCoinButton: document.getElementById('use-coin-button'),
        levelDisplay: document.getElementById('level'),
        stageDisplay: document.getElementById('stage'),
        gridSizeDisplay: document.getElementById('grid-size'),
        scoreDisplay: document.getElementById('score'),
        timerDisplay: document.getElementById('timer'),
        statusMessage: document.getElementById('status-message'),
        musicToggle: document.getElementById('music-toggle'),
        musicIcon: document.getElementById('music-icon'),
        backgroundMusic: document.getElementById('background-music'),
        clickSound: document.getElementById('click-sound'),
        successSound: document.getElementById('success-sound'),
        errorSound: document.getElementById('error-sound'),
        bestScore: document.getElementById('best-score'),
        maxLevel: document.getElementById('max-level'),
        maxGridSize: document.getElementById('max-grid-size'),
        gamesPlayed: document.getElementById('games-played'),
        coinDisplay: document.getElementById('coin-display'),
        gameOverModal: document.getElementById('game-over-modal'),
        finalScore: document.getElementById('final-score'),
        finalLevel: document.getElementById('final-level'),
        finalGridSize: document.getElementById('final-grid-size'),
        playAgainButton: document.getElementById('play-again-button'),
        shareButton: document.getElementById('share-button'),
        timerProgress: document.getElementById('timer-progress')
    };

    // O'yin sozlamalari
    const gameConfig = {
        currentLevel: 1,
        currentStage: 1,
        stagesPerLevel: 5,
        maxLevel: 10,
        score: 0,
        sequence: [],
        playerSequence: [],
        isShowingSequence: false,
        canPlayerClick: false,
        timerInterval: null,
        timeLeft: 0,
        gameStartTime: null,
        musicEnabled: false,
        gameOver: false,
        hasProgress: false,
        progressData: null,

        // Katakchalar soni darajaga qarab
        getGridSize(level) {
            return level + 2;
        },

        // Har bir darajadagi ketma-ketlik uzunligi
        getSequenceLength(level, stage) {
            const baseLength = Math.min(5, level + 2);
            return baseLength + Math.floor(stage / 2);
        },

        // Har bir darajadagi yonish vaqti (millisekundlarda)
        getFlashTime(level) {
            return Math.max(400, 1200 - (level - 1) * 80);
        },

        // O'yinchi uchun javob berish vaqti (sekundlarda)
        getAnswerTime(level, sequenceLength) {
            return Math.max(5, sequenceLength * 2 + level);
        }
    };

    // Foydalanuvchi statistikasini yuklash
    async function loadUserStats() {
        try {
            const response = await fetch('/api/user-stats');
            if (response.ok) {
                const stats = await response.json();
                elements.bestScore.textContent = stats.best_score;
                elements.maxLevel.textContent = stats.max_level;
                elements.maxGridSize.textContent = `${stats.max_grid_size}×${stats.max_grid_size}`;
                elements.gamesPlayed.textContent = stats.games_played;
                elements.coinDisplay.textContent = stats.coins;
            }
        } catch (error) {
            console.error('Failed to load user stats:', error);
        }
    }

    // Previous game progress check
    async function checkGameProgress() {
        try {
            const response = await fetch('/api/get-progress');
            if (response.ok) {
                const data = await response.json();
                
                if (data.status === 'success' && data.has_progress) {
                    gameConfig.hasProgress = true;
                    gameConfig.progressData = data.progress;
                    
                    // Show continue button
                    elements.continueButton.classList.remove('hidden');
                    elements.useCoinButton.classList.remove('hidden');
                }
            }
        } catch (error) {
            console.error('Failed to check game progress:', error);
        }
    }

    // Load saved game
    function loadSavedGame() {
        if (!gameConfig.progressData) return;
        
        gameConfig.currentLevel = gameConfig.progressData.level;
        gameConfig.currentStage = gameConfig.progressData.stage;
        gameConfig.score = gameConfig.progressData.score;
        gameConfig.sequence = gameConfig.progressData.sequence;
        
        createGrid();
        updateDisplay();
        
        elements.statusMessage.textContent = "Saqlangan o'yin yuklandi. Davom etishga tayyormisiz?";
        elements.statusMessage.className = "text-lg font-medium text-center text-blue-400 mb-6 p-4 bg-blue-900/30 rounded-lg border border-blue-700";
        
        startGame(true); // true - continue from saved game
    }

    // O'yin maydoni katakchalarini yaratish
    function createGrid() {
        elements.gameContainer.innerHTML = '';
        const gridSize = gameConfig.getGridSize(gameConfig.currentLevel);
        elements.gridSizeDisplay.textContent = `${gridSize}×${gridSize}`;

        // Konteyner o'lchamini darajaga qarab moslash
        const maxCellSize = 80; // Maksimal katakcha o'lchami (pixels)
        const containerSize = Math.min(window.innerWidth * 0.8, 600); // Konteyner o'lchami
        const cellSize = Math.min(maxCellSize, Math.floor(containerSize / gridSize) - 4);

        const grid = document.createElement('div');
        grid.className = 'grid gap-1';
        grid.style.gridTemplateColumns = `repeat(${gridSize}, 1fr)`;
        grid.style.maxWidth = `${containerSize}px`;
        grid.style.margin = '0 auto';

        for (let i = 0; i < gridSize * gridSize; i++) {
            const cell = document.createElement('div');
            cell.className = 'bg-gray-700 hover:bg-gray-600 rounded-lg cursor-pointer transition-colors duration-100';
            cell.style.width = `${cellSize}px`;
            cell.style.height = `${cellSize}px`;
            cell.dataset.index = i;
            cell.addEventListener('click', handleCellClick);
            grid.appendChild(cell);
        }

        elements.gameContainer.appendChild(grid);
    }

    // Tasodifiy ketma-ketlik yaratish
    function generateSequence() {
        const gridSize = gameConfig.getGridSize(gameConfig.currentLevel);
        const totalCells = gridSize * gridSize;
        const sequenceLength = gameConfig.getSequenceLength(gameConfig.currentLevel, gameConfig.currentStage);

        gameConfig.sequence = [];

        for (let i = 0; i < sequenceLength; i++) {
            const randomIndex = Math.floor(Math.random() * totalCells);
            gameConfig.sequence.push(randomIndex);
        }
    }

    // Ketma-ketlikni ko'rsatish
    function showSequence() {
        gameConfig.isShowingSequence = true;
        gameConfig.canPlayerClick = false;
        elements.statusMessage.textContent = "Diqqat bilan kuzating...";
        elements.statusMessage.className = "text-lg font-medium text-center text-yellow-400 mb-6 p-4 bg-yellow-900/30 rounded-lg border border-yellow-700";

        let currentIndex = 0;
        const flashTime = gameConfig.getFlashTime(gameConfig.currentLevel);

        const sequenceInterval = setInterval(() => {
            if (currentIndex < gameConfig.sequence.length) {
                // Barcha katakchalarni o'chirib qo'yish
                const cells = elements.gameContainer.querySelectorAll('div[data-index]');
                cells.forEach(cell => {
                    cell.classList.remove('bg-blue-500', 'animate-glow');
                    cell.classList.add('bg-gray-700');
                });

                // Hozirgi ketma-ketlikni yoqish
                const index = gameConfig.sequence[currentIndex];
                const cell = elements.gameContainer.querySelector(`div[data-index="${index}"]`);
                cell.classList.remove('bg-gray-700');
                cell.classList.add('bg-blue-500', 'animate-glow');

                // Tovush chiqarish
                if (gameConfig.musicEnabled) {
                    elements.clickSound.currentTime = 0;
                    elements.clickSound.play();
                }

                // Yongan katakchani o'chirish
                setTimeout(() => {
                    cell.classList.remove('bg-blue-500', 'animate-glow');
                    cell.classList.add('bg-gray-700');
                }, flashTime * 0.7);

                currentIndex++;
            } else {
                clearInterval(sequenceInterval);
                gameConfig.isShowingSequence = false;
                gameConfig.canPlayerClick = true;
                gameConfig.playerSequence = [];

                elements.statusMessage.textContent = "Endi ketma-ketlikni takrorlang!";
                elements.statusMessage.className = "text-lg font-medium text-center text-green-400 mb-6 p-4 bg-green-900/30 rounded-lg border border-green-700";
                startTimer();
            }
        }, flashTime);
    }

    // Timer boshlash
    function startTimer() {
        if (gameConfig.timerInterval) {
            clearInterval(gameConfig.timerInterval);
        }

        const sequenceLength = gameConfig.sequence.length;
        gameConfig.timeLeft = gameConfig.getAnswerTime(gameConfig.currentLevel, sequenceLength);
        elements.timerDisplay.textContent = gameConfig.timeLeft;

        // Reset animation
        elements.timerProgress.style.width = '100%';
        elements.timerProgress.classList.remove('countdown-active');
        void elements.timerProgress.offsetWidth; // Trigger reflow
        
        // Set animation duration
        elements.timerProgress.style.animationDuration = `${gameConfig.timeLeft}s`;
        elements.timerProgress.classList.add('countdown-active');

        gameConfig.timerInterval = setInterval(() => {
            gameConfig.timeLeft--;
            elements.timerDisplay.textContent = gameConfig.timeLeft;

            if (gameConfig.timeLeft <= 0) {
                clearInterval(gameConfig.timerInterval);
                gameOver("Vaqt tugadi!");
            }
        }, 1000);
    }

    // Katak bosilgandagi harakat
    function handleCellClick(event) {
        if (!gameConfig.canPlayerClick || gameConfig.isShowingSequence) return;

        const clickedIndex = parseInt(event.target.dataset.index);
        gameConfig.playerSequence.push(clickedIndex);

        // Visual feedback
        event.target.classList.remove('bg-gray-700');
        event.target.classList.add('bg-blue-500', 'animate-glow');

        // Tovush chiqarish
        if (gameConfig.musicEnabled) {
            elements.clickSound.currentTime = 0;
            elements.clickSound.play();
        }

        setTimeout(() => {
            event.target.classList.remove('bg-blue-500', 'animate-glow');
            event.target.classList.add('bg-gray-700');
        }, 300);

        // Tekshirish
        const currentIndex = gameConfig.playerSequence.length - 1;

        // Xato kiritilgan
        if (gameConfig.playerSequence[currentIndex] !== gameConfig.sequence[currentIndex]) {
            if (gameConfig.musicEnabled) {
                elements.errorSound.currentTime = 0;
                elements.errorSound.play();
            }
            gameOver("Xato! Qayta urining.");
            return;
        }

        // To'g'ri kiritilgan, ketma-ketlik to'liq
        if (gameConfig.playerSequence.length === gameConfig.sequence.length) {
            clearInterval(gameConfig.timerInterval);

            if (gameConfig.musicEnabled) {
                elements.successSound.currentTime = 0;
                elements.successSound.play();
            }

            // O'yin davom etish
            gameConfig.score += gameConfig.currentLevel * gameConfig.currentStage * 10;
            elements.scoreDisplay.textContent = gameConfig.score;

            gameConfig.currentStage++;

            // Save game progress
            saveGameProgress();

            // Add coins for completing a stage
            addCoinsForStage();

            // Daraja tugagan bo'lsa, yangi darajaga o'tish
            if (gameConfig.currentStage > gameConfig.stagesPerLevel) {
                gameConfig.currentStage = 1;
                gameConfig.currentLevel++;
                
                // O'yin tugagan
                if (gameConfig.currentLevel > gameConfig.maxLevel) {
                    gameWin();
                    return;
                }

                createGrid();
            }

            updateDisplay();
            elements.statusMessage.textContent = "Juda yaxshi! Keyingi bosqichga tayyorlaning...";
            elements.statusMessage.className = "text-lg font-medium text-center text-green-400 mb-6 p-4 bg-green-900/30 rounded-lg border border-green-700";

            setTimeout(() => {
                startGame();
            }, 1500);
        }
    }

    // Add coins for completing a stage
    async function addCoinsForStage() {
        try {
            const result = {
                score: gameConfig.score,
                level: gameConfig.currentLevel,
                stage: gameConfig.currentStage - 1, // We already incremented the stage
                grid_size: gameConfig.getGridSize(gameConfig.currentLevel),
                duration: Math.floor((Date.now() - gameConfig.gameStartTime) / 1000),
                completed: true
            };

            const response = await fetch('/api/save-result', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(result)
            });

            if (response.ok) {
                const data = await response.json();
                // Update coin display
                elements.coinDisplay.textContent = data.total_coins;

                // Show coin animation
                if (data.coins_added > 0) {
                    const coinAddedMessage = document.createElement('div');
                    coinAddedMessage.className = 'fixed top-20 right-10 bg-yellow-900/70 text-yellow-300 px-4 py-2 rounded-lg z-50 animate-bounce-slow';
                    coinAddedMessage.innerHTML = `<i class="fas fa-coins mr-2"></i> +${data.coins_added} coin`;
                    document.body.appendChild(coinAddedMessage);

                    setTimeout(() => {
                        coinAddedMessage.remove();
                    }, 2000);
                }
            }
        } catch (error) {
            console.error('Error saving result:', error);
        }
    }

    // Save game progress
    async function saveGameProgress() {
        if (gameConfig.gameOver) return;

        try {
            const progress = {
                level: gameConfig.currentLevel,
                stage: gameConfig.currentStage,
                grid_size: gameConfig.getGridSize(gameConfig.currentLevel),
                score: gameConfig.score,
                sequence: gameConfig.sequence
            };

            await fetch('/api/save-progress', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(progress)
            });
        } catch (error) {
            console.error('Error saving game progress:', error);
        }
    }

    // Use coins to continue game
    async function useCoinsAndContinue() {
        try {
            const response = await fetch('/api/use-coins', {
                method: 'POST'
            });

            const data = await response.json();
            
            if (response.ok) {
                // Update coin display
                elements.coinDisplay.textContent = data.remaining_coins;
                
                // If we have saved progress, load it
                if (gameConfig.hasProgress) {
                    loadSavedGame();
                    
                    // Close modal if it's open
                    elements.gameOverModal.classList.add('hidden');
                    
                    // Show success message
                    const coinUsedMessage = document.createElement('div');
                    coinUsedMessage.className = 'fixed top-20 right-10 bg-green-900/70 text-green-300 px-4 py-2 rounded-lg z-50';
                    coinUsedMessage.innerHTML = `<i class="fas fa-coins mr-2"></i> ${data.message}`;
                    document.body.appendChild(coinUsedMessage);

                    setTimeout(() => {
                        coinUsedMessage.remove();
                    }, 3000);
                }
            } else {
                // Show error message
                const coinErrorMessage = document.createElement('div');
                coinErrorMessage.className = 'fixed top-20 right-10 bg-red-900/70 text-red-300 px-4 py-2 rounded-lg z-50';
                coinErrorMessage.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i> ${data.message}`;
                document.body.appendChild(coinErrorMessage);

                setTimeout(() => {
                    coinErrorMessage.remove();
                }, 3000);
            }
        } catch (error) {
            console.error('Error using coins:', error);
        }
    }

    // O'yin tugadi
    function gameOver(message) {
        gameConfig.gameOver = true;
        gameConfig.canPlayerClick = false;
        clearInterval(gameConfig.timerInterval);

        const gameDuration = Math.floor((Date.now() - gameConfig.gameStartTime) / 1000);

        // Save game progress for continue feature
        saveGameProgress();

        elements.statusMessage.textContent = message;
        elements.statusMessage.className = "text-lg font-medium text-center text-red-400 mb-6 p-4 bg-red-900/30 rounded-lg border border-red-700";

        elements.startButton.classList.add('hidden');
        elements.restartButton.classList.remove('hidden');
        elements.useCoinButton.classList.remove('hidden');

        // Show game over modal
        elements.finalScore.textContent = gameConfig.score;
        elements.finalLevel.textContent = gameConfig.currentLevel;
        elements.finalGridSize.textContent = `${gameConfig.getGridSize(gameConfig.currentLevel)}×${gameConfig.getGridSize(gameConfig.currentLevel)}`;
        elements.gameOverModal.classList.remove('hidden');

        // Play error sound
        if (gameConfig.musicEnabled) {
            elements.errorSound.currentTime = 0;
            elements.errorSound.play();
        }
    }

    // O'yin g'alaba
    function gameWin() {
        gameConfig.gameOver = true;
        clearInterval(gameConfig.timerInterval);

        const gameDuration = Math.floor((Date.now() - gameConfig.gameStartTime) / 1000);

        elements.statusMessage.textContent = "Tabriklaymiz! Barcha darajalarni yakunladingiz!";
        elements.statusMessage.className = "text-lg font-medium text-center text-green-400 mb-6 p-4 bg-green-900/30 rounded-lg border border-green-700";

        elements.startButton.classList.add('hidden');
        elements.restartButton.classList.remove('hidden');

        // Play success sound
        if (gameConfig.musicEnabled) {
            elements.successSound.currentTime = 0;
            elements.successSound.play();
        }

        // Save final result
        const result = {
            score: gameConfig.score,
            level: gameConfig.currentLevel,
            stage: gameConfig.currentStage,
            grid_size: gameConfig.getGridSize(gameConfig.currentLevel),
            duration: gameDuration,
            completed: true
        };

        saveGameResult(result);
    }

    // Natijani serverga saqlash
    async function saveGameResult(result) {
        try {
            const response = await fetch('/api/save-result', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(result)
            });

            if (response.ok) {
                // Statistikani qayta yuklash
                loadUserStats();
            } else {
                console.error('Failed to save game result');
            }
        } catch (error) {
            console.error('Error saving game result:', error);
        }
    }

    // Ekrandagi ma'lumotlarni yangilash
    function updateDisplay() {
        elements.levelDisplay.textContent = gameConfig.currentLevel;
        elements.stageDisplay.textContent = gameConfig.currentStage;
        elements.scoreDisplay.textContent = gameConfig.score;
        elements.gridSizeDisplay.textContent = `${gameConfig.getGridSize(gameConfig.currentLevel)}×${gameConfig.getGridSize(gameConfig.currentLevel)}`;
    }

    // O'yinni boshlash
    function startGame(fromSaved = false) {
        gameConfig.gameOver = false;
        gameConfig.canPlayerClick = false;
        gameConfig.gameStartTime = Date.now();

        elements.statusMessage.textContent = "Tayyor bo'ling...";
        elements.statusMessage.className = "text-lg font-medium text-center text-blue-400 mb-6 p-4 bg-blue-900/30 rounded-lg border border-blue-700";

        elements.startButton.classList.add('hidden');
        elements.continueButton.classList.add('hidden');
        elements.restartButton.classList.add('hidden');
        elements.useCoinButton.classList.add('hidden');

        if (!fromSaved) {
            generateSequence();
        }

        setTimeout(() => {
            showSequence();
        }, 1000);
    }

    // O'yinni qayta boshlash
    function restartGame() {
        gameConfig.currentLevel = 1;
        gameConfig.currentStage = 1;
        gameConfig.score = 0;
        gameConfig.sequence = [];
        gameConfig.playerSequence = [];
        gameConfig.gameOver = false;

        elements.startButton.classList.remove('hidden');
        elements.restartButton.classList.add('hidden');
        elements.useCoinButton.classList.add('hidden');
        elements.gameOverModal.classList.add('hidden');

        createGrid();
        updateDisplay();

        elements.statusMessage.textContent = "Tayyor bo'lganingizda \"Boshlash\" tugmasini bosing";
        elements.statusMessage.className = "text-lg font-medium text-center text-gray-400 mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700";

        // Check if there's saved progress
        checkGameProgress();
    }

    // Musiqani yoqish/o'chirish
    function toggleMusic() {
        gameConfig.musicEnabled = !gameConfig.musicEnabled;

        if (gameConfig.musicEnabled) {
            elements.musicIcon.className = 'fas fa-volume-up';
            elements.backgroundMusic.play();
        } else {
            elements.musicIcon.className = 'fas fa-volume-mute';
            elements.backgroundMusic.pause();
        }
    }

    // Event listeners
    elements.startButton.addEventListener('click', () => startGame(false));
    elements.continueButton.addEventListener('click', () => loadSavedGame());
    elements.restartButton.addEventListener('click', restartGame);
    elements.useCoinButton.addEventListener('click', useCoinsAndContinue);
    elements.playAgainButton.addEventListener('click', () => {
        elements.gameOverModal.classList.add('hidden');
        restartGame();
    });
    elements.musicToggle.addEventListener('click', toggleMusic);
    elements.shareButton.addEventListener('click', () => {
        // Share functionality would go here
        alert('Ulashish funksiyasi tez orada qo\'shiladi!');
    });

    // Dastlabki sozlash
    createGrid();
    updateDisplay();
    loadUserStats();
    checkGameProgress();

    // Quyidagi qator bilan brauzerning o'z xususiyatlari bilan o'yinni ochib olishi oldini olamiz
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i')) ||
            (e.ctrlKey && e.shiftKey && (e.key === 'J' || e.key === 'j')) ||
            (e.key === 'F12')) {
            e.preventDefault();
        }
    });
});