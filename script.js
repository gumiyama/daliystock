document.addEventListener('DOMContentLoaded', () => {
    const chartCanvas = document.getElementById('stockChart');
    const tickerNameElement = document.getElementById('ticker-name');
    const currentPriceElement = document.getElementById('current-price');
    const previousCloseElement = document.getElementById('previous-close');
    const tabContainer = document.querySelector('.tab-container');
    const newTickerInput = document.getElementById('new-ticker-input');
    const addTickerButton = document.getElementById('add-ticker-button');

    let currentChart = null;
    let activeTicker = null;

    async function fetchStockData(ticker) {
        try {
            // Flaskサーバーはポート5001で動作していると仮定
            const response = await fetch(`http://localhost:5001/api/stock_data/${ticker}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            // console.log(`Data for ${ticker}:`, data); // デバッグ用
            return data;
        } catch (error) {
            console.error(`Could not fetch stock data for ${ticker}:`, error);
            tickerNameElement.textContent = `銘柄名: ${ticker} (データ取得エラー)`;
            currentPriceElement.textContent = '現在値: -';
            previousCloseElement.textContent = '前日終値: -';
            if (currentChart) {
                currentChart.destroy(); // エラー時はチャートをクリア
                currentChart = null; // 破棄したことを明示
            }
            return null;
        }
    }

    function updateStockInfo(data) {
        if (!data) return;

        tickerNameElement.textContent = `銘柄名: ${data.name || data.ticker}`;
        currentPriceElement.textContent = `現在値: ${data.current_price !== null && data.current_price !== undefined ? data.current_price.toFixed(2) : '-'}`;
        previousCloseElement.textContent = `前日終値: ${data.previous_close !== null && data.previous_close !== undefined ? data.previous_close.toFixed(2) : '-'}`;
    }

    async function displayChart(ticker) {
        const stockData = await fetchStockData(ticker);

        if (currentChart) {
            currentChart.destroy();
            currentChart = null;
        }

        // 既存のキャンバスを取得し、親要素を取得
        const chartContainer = chartCanvas.parentElement;
        // 以前のエラーメッセージがあれば削除
        const existingErrorMsg = chartContainer.querySelector('.chart-error-message');
        if (existingErrorMsg) {
            existingErrorMsg.remove();
        }
        // チャートキャンバスは常に表示状態に戻す（エラーメッセージと切り替えるため）
        chartCanvas.style.display = '';


        if (!stockData || !stockData.chart_data || stockData.chart_data.length === 0) {
            console.warn(`No chart data or empty chart data for ${ticker}`);
            // 銘柄情報エリアは更新する (エラー情報を含む可能性も考慮)
            updateStockInfo(stockData || {
                ticker: ticker,
                name: stockData?.name || ticker, // APIからのエラーの場合nameがないことも
                current_price: null,
                previous_close: null
            });
            activeTicker = ticker; // エラーの場合もactiveTickerは更新しておく

            // チャートエリアにエラーメッセージを表示
            const errorMsgElement = document.createElement('p');
            let message = `銘柄「${ticker}」のチャートデータを取得できませんでした。`;
            if (stockData && stockData.error) {
                message += ` (エラー: ${stockData.error})`;
            } else {
                message += " 銘柄コードが正しいか、ネットワーク接続を確認してください。";
            }
            errorMsgElement.textContent = message;
            errorMsgElement.className = 'chart-error-message'; // スタイル付け用

            // canvasを非表示にしてメッセージを表示
            chartCanvas.style.display = 'none';
            chartContainer.appendChild(errorMsgElement);
            return;
        }

        activeTicker = ticker; // 正常にデータ取得できた場合に設定
        updateStockInfo(stockData);

        const labels = stockData.chart_data.map(d => d.date);
        const prices = stockData.chart_data.map(d => d.close);

        // if (currentChart) { // 既に冒頭でdestroyしているので不要
        //     currentChart.destroy();
        //     currentChart = null;
        // }

        const ctx = chartCanvas.getContext('2d');
        // console.log("Creating new chart for", ticker);
        currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${stockData.name || ticker} 終値`,
                    data: prices,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)', // 少し背景色を追加
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true, // 線の下を塗りつぶす
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // これが重要。コンテナに合わせて伸縮する
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '日付'
                        },
                        ticks: {
                            maxRotation: 0, // ラベルの回転を防ぐ
                            autoSkip: true, // ラベルを自動的に間引く
                            maxTicksLimit: 10 // 表示するX軸ラベルの最大数 (適宜調整)
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '株価'
                        },
                        beginAtZero: false // Y軸の開始を0にしない
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                animation: {
                    duration: 500 // アニメーション時間を少し短く
                }
            }
        });
    }

    function setActiveTab(tabElement) {
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        if (tabElement) {
            tabElement.classList.add('active');
        }
    }

    // この関数はステップ6の銘柄追加機能で主に使用されます。
    // このステップでは、既存のタブ機能との連携をスムーズにするための準備として定義します。
    function addTab(ticker, setActive = true) {
        const existingTab = tabContainer.querySelector(`.tab-button[data-ticker="${ticker}"]`);
        if (existingTab) {
            if (setActive) {
                setActiveTab(existingTab);
                displayChart(ticker); // 既存タブでもチャートは更新
            }
            return existingTab;
        }

        const tabButton = document.createElement('button');
        tabButton.classList.add('tab-button');
        tabButton.dataset.ticker = ticker;
        tabButton.textContent = ticker;

        // オプション: タブ削除ボタンの追加 (今回はコメントアウト)
        // const closeButton = document.createElement('span');
        // closeButton.textContent = ' \u00D7'; // ×記号
        // closeButton.style.marginLeft = '5px';
        // closeButton.style.cursor = 'pointer';
        // closeButton.addEventListener('click', (event) => {
        //     event.stopPropagation(); // 親のタブクリックイベントを止める
        //     removeTab(ticker);
        // });
        // tabButton.appendChild(closeButton);

        tabContainer.appendChild(tabButton);

        if (setActive) {
            setActiveTab(tabButton);
            displayChart(ticker);
        }
        return tabButton;
    }

    // オプション: removeTab 関数の雛形 (今回はコメントアウト)
    // function removeTab(ticker) {
    //     const tabToRemove = tabContainer.querySelector(`.tab-button[data-ticker="${ticker}"]`);
    //     if (tabToRemove) {
    //         const isActive = tabToRemove.classList.contains('active');
    //         const nextActiveTab = tabToRemove.nextElementSibling || tabToRemove.previousElementSibling;
    //         tabToRemove.remove();
    //         activeTicker = null; // アクティブティッカーをリセット
    //         if (isActive) {
    //             if (nextActiveTab && nextActiveTab.classList.contains('tab-button')) {
    //                 setActiveTab(nextActiveTab);
    //                 displayChart(nextActiveTab.dataset.ticker);
    //             } else {
    //                 const firstTab = tabContainer.querySelector('.tab-button');
    //                 if (firstTab) {
    //                     setActiveTab(firstTab);
    //                     displayChart(firstTab.dataset.ticker);
    //                 } else {
    //                     if (currentChart) { currentChart.destroy(); currentChart = null; }
    //                     updateStockInfo({ name: '-', ticker: '', current_price: null, previous_close: null });
    //                 }
    //             }
    //         }
    //     }
    // }


    // タブクリックイベントリスナーの更新
    tabContainer.addEventListener('click', (event) => {
        const targetTab = event.target.closest('.tab-button'); // ボタン内の要素クリックにも対応
        if (targetTab) {
            const ticker = targetTab.dataset.ticker;
            if (ticker && ticker !== activeTicker) { // クリックされたのが別ティッカーのタブの場合のみ更新
                setActiveTab(targetTab);
                displayChart(ticker);
            } else if (ticker && ticker === activeTicker) {
                // 必要であれば、同じタブをクリックした際にデータを再取得するなどの処理も入れられる
                // console.log("Same tab clicked, potentially refresh data or do nothing.");
                // displayChart(ticker); // 強制的に再描画・データ更新する場合
            }
        }
    });

    // 銘柄追加ボタンの処理
    addTickerButton.addEventListener('click', () => {
        const newTicker = newTickerInput.value.trim().toUpperCase();
        if (newTicker) {
            // yfinanceでは、日本の銘柄コードに ".T" をつけることが多いので、
            // ユーザーが数字4桁で入力した場合、自動で ".T" を付与する補助機能 (オプション)
            // if (/^\d{4}$/.test(newTicker)) {
            //     newTicker += ".T";
            // }

            const existingTab = tabContainer.querySelector(`.tab-button[data-ticker="${newTicker}"]`);
            if (existingTab) {
                setActiveTab(existingTab); // 既存のタブをアクティブにする
                displayChart(newTicker);    // チャートを再表示/更新
                // alert(`銘柄 ${newTicker} は既にタブリストに存在します。`);
                console.log(`Ticker ${newTicker} already exists. Activating it.`);
            } else {
                addTab(newTicker, true); // 新しいタブを追加してアクティブにする
            }
            newTickerInput.value = ''; // 入力欄をクリア
        } else {
            alert('銘柄コードを入力してください。');
        }
    });


    // 初期表示ロジックの更新
    let initialTabToDisplay = tabContainer.querySelector('.tab-button.active');
    if (!initialTabToDisplay) {
        initialTabToDisplay = tabContainer.querySelector('.tab-button'); // アクティブがなければ最初のタブ
    }

    if (initialTabToDisplay) {
        setActiveTab(initialTabToDisplay); // これで active クラスが付与される
        displayChart(initialTabToDisplay.dataset.ticker);
    } else {
        console.log("No initial tabs found. Consider adding a default tab.");
        // 例: デフォルトで 'AAPL' のタブを追加して表示
        // addTab("AAPL", true);
    }
});
