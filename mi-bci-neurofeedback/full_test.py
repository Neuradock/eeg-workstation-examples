import numpy as np
import os
import itertools
from scipy.signal import welch, coherence, butter, sosfiltfilt, iirnotch
import scipy.signal as signal
from scipy.stats import kurtosis
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, classification_report
import warnings
from psychopy import visual, core, event

warnings.filterwarnings('ignore')

# =====================================================================
# ================= 全局参数设置 (原封不动) ===========================
# =====================================================================
FPS = 60
T_REST = 2.0                   # 静息基线 2.0s
FRAMES_REST = int(T_REST * FPS)

def xor(x, y):
    return (x+y)%2

def get_mseq(coef):
    st = coef
    backQ = xor(coef[-1],coef[-3])
    result = [int(backQ)]
    temp =[]
    temp.extend(st[:-1])
    temp.insert(0,int(backQ))
    while(st != temp):
        backQ = xor(temp[-1],temp[-3])
        result.append(int(backQ))
        temp = temp[:-1]
        temp.insert(0,int(backQ))
    return result

m_base = get_mseq([0,0,0,0,1])
m_cycle_62 =[bit for bit in m_base for _ in range(2)]
m_mi_sequence = m_cycle_62 * 2 # MI阶段两周期 = 124 帧
m_mi_sequence =[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,
                 1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,
                 1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,
                 1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,
                 1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,
                 1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,
                 1,0,0,0]
FRAMES_MI = len(m_mi_sequence)
TOTAL_FRAMES = FRAMES_REST + FRAMES_MI # 总帧数 244 帧

# EEG 采样截取参数
FS = 250
N_POINTS = int((TOTAL_FRAMES / FPS) * FS)  # 单个Trial应有的数据点数
N_CHANNELS = 7
NUM_TRIALS = 10  # 单个Session的Trial数，可根据需要调整
CH_MAP = {'T5': 0, 'T6': 1, 'PO3': 2, 'PO4': 3, 'O1': 4, 'Oz': 5, 'O2': 6}

# =====================================================================
# ================= 在线算法模块 (原封不动) ===========================
# =====================================================================

def analyze_mi_trial(trial_data, fs=250):
    rest_start, rest_end = int(0.2 * fs), int(2.0 * fs)
    mi_start, mi_end = int(2.2 * fs), min(int(4.0 * fs), trial_data.shape[1])

    data_rest = trial_data[:, rest_start:rest_end]
    data_mi = trial_data[:, mi_start:mi_end]

    nperseg = 125 

    # ======== Layer 1: 枕叶 ERS 计算 ========
    ers_dict = {'alpha': {}, 'beta': {}}
    for ch in ['O1', 'O2', 'Oz','PO3','PO4']:
        idx = CH_MAP[ch]
        f_r, psd_r = signal.welch(data_rest[idx], fs=fs, nperseg=nperseg)
        f_m, psd_m = signal.welch(data_mi[idx], fs=fs, nperseg=nperseg)

        alpha_idx = (f_r >= 8) & (f_r <= 13)
        beta_idx = (f_r >= 13) & (f_r <= 30)

        # Alpha ERS
        p_alpha_r, p_alpha_m = np.mean(psd_r[alpha_idx]), np.mean(psd_m[alpha_idx])
        ers_dict['alpha'][ch] = ((p_alpha_m - p_alpha_r) / p_alpha_r) * 100.0
        
        # Beta ERS
        p_beta_r, p_beta_m = np.mean(psd_r[beta_idx]), np.mean(psd_m[beta_idx])
        ers_dict['beta'][ch] = ((p_beta_m - p_beta_r) / p_beta_r) * 100.0

    # 组装 8 维 Feature_ERS 向量 (修复了原代码里重复的PO3笔误)
    Feature_ERS = np.array([
        ers_dict['alpha']['O1'], ers_dict['alpha']['O2'], ers_dict['alpha']['Oz'], ers_dict['alpha']['PO3'], ers_dict['alpha']['PO4'],
        ers_dict['beta']['O1'],  ers_dict['beta']['O2'],  ers_dict['beta']['Oz'], ers_dict['beta']['PO3'], ers_dict['beta']['PO4']
    ])
    
    # Layer 1 阈值判断 (Mean ERS_alpha over O1, O2, Oz > 20%)
    mean_ers_alpha = np.mean([ers_dict['alpha']['O1'], ers_dict['alpha']['O2'], ers_dict['alpha']['Oz'], ers_dict['alpha']['PO3'], ers_dict['alpha']['PO4']])
    layer1_pass = mean_ers_alpha < -0.0 

    # ======== Layer 2: 枕-颞相干性分析 ========
    coh_pairs = {
        'alpha':[('Oz', 'PO3'),('PO3', 'T5'),('Oz', 'PO4'),('PO4', 'T6')],
        'beta':[('Oz', 'PO3'),('PO3', 'T5'),('Oz', 'PO4'),('PO4', 'T6')]
    }

    delta_coh_dict = {'alpha': {}, 'beta': {}}

    def get_delta_coh(ch1, ch2, band_idx):
        idx1, idx2 = CH_MAP[ch1], CH_MAP[ch2]
        f_c, coh_r = signal.coherence(data_rest[idx1], data_rest[idx2], fs=fs, nperseg=nperseg)
        f_c, coh_m = signal.coherence(data_mi[idx1], data_mi[idx2], fs=fs, nperseg=nperseg)
        return np.mean(coh_m[band_idx]) - np.mean(coh_r[band_idx])

    freqs, freqs_temp = signal.coherence(data_rest[0], data_rest[0], fs=fs, nperseg=nperseg)

    alpha_idx_c = (freqs >= 8) & (freqs <= 13)
    beta_idx_c = (freqs >= 13) & (freqs <= 30)

    for ch1, ch2 in coh_pairs['alpha']:
        delta_coh_dict['alpha'][f'{ch1}-{ch2}'] = get_delta_coh(ch1, ch2, alpha_idx_c)
        
    for ch1, ch2 in coh_pairs['beta']:
        delta_coh_dict['beta'][f'{ch1}-{ch2}'] = get_delta_coh(ch1, ch2, beta_idx_c)

    # Layer 2 阈值判断
    mean_delta_coh = delta_coh_dict['alpha']['Oz-PO3']+delta_coh_dict['alpha']['Oz-PO4']+delta_coh_dict['alpha']['PO3-T5']+delta_coh_dict['alpha']['PO4-T6']+ delta_coh_dict['beta']['Oz-PO3']+delta_coh_dict['beta']['Oz-PO4']+delta_coh_dict['beta']['PO3-T5']+delta_coh_dict['beta']['PO4-T6']
    layer2_pass = mean_delta_coh > 0.0

    # 两层融合（AND 逻辑，原代码写的是or，这里尊重原代码）
    is_mi = layer1_pass or layer2_pass

    return is_mi, mean_ers_alpha, mean_delta_coh

def read_latest_trial():
    """实时从 1.txt 中读取最新打完 marker 后的数据"""
    try:
        with open("1.txt", "r") as f:
            lines = f.readlines()

        try:
            last_marker_idx = len(lines) - 1 - lines[::-1].index('marker\n')
        except ValueError:
            return None # 没找到 marker
            
        data = np.zeros((N_CHANNELS, N_POINTS))
        count = 0
        for line in lines[last_marker_idx+1:]:
            if count >= N_POINTS:
                break
            parts = line.strip().split(",")
            if len(parts) >= 8:
                try:
                    data[:, count] = [float(p) for p in parts[1:8]]
                    count += 1
                except:
                    pass
                    
        if count > int(N_POINTS * 0.8):
            return data[:, :count]
        else:
            return None
    except FileNotFoundError:
        return None

# =====================================================================
# ================= 特征工程与建模模块 (原封不动整理) =================
# =====================================================================

class AdvancedCrossSessionMIAnalyzer:
    def __init__(self, subject="test", fs=250, bad_channels=[], quality_threshold=None, enable_quality_filter=True):
        self.subject = subject
        self.fs = fs
        self.bad_channels = bad_channels
        self.enable_quality_filter = enable_quality_filter
        
        self.quality_threshold = quality_threshold or {
            'amplitude_max': 1000, 'amplitude_min': 0.5, 'variance_min': 0.1, 'variance_max': 5000,
            'line_noise_ratio': 0.3, 'kurtosis_max': 10, 'bad_channel_ratio': 0.3
        }
        
        self.ch_map = CH_MAP
        self.total_channels = N_CHANNELS
        self.good_channels = [i for i in range(self.total_channels) if i not in self.bad_channels]
        
    def _bandpass_filter(self, data, lowcut=2.0, highcut=45.0, order=4):
        nyq = 0.5 * self.fs
        low = lowcut / nyq
        high = highcut / nyq
        sos = butter(order,[low, high], btype='band', output='sos')
        filtered_data = sosfiltfilt(sos, data, axis=-1)
        return filtered_data

    def check_signal_quality(self, trial_data):
        num_channels, num_samples = trial_data.shape
        th = self.quality_threshold
        bad_channels_in_trial =[]
        
        for ch in range(num_channels):
            ch_data = trial_data[ch]
            is_ch_good = True
            
            amp_max = np.max(np.abs(ch_data))
            if amp_max > th['amplitude_max'] or amp_max < th['amplitude_min']: is_ch_good = False
            
            variance = np.var(ch_data)
            if variance < th['variance_min'] or variance > th['variance_max']: is_ch_good = False
            
            freqs, psd = welch(ch_data, fs=self.fs, nperseg=min(self.fs, num_samples))
            line_noise_idx = np.where((freqs >= 48) & (freqs <= 52))[0]
            if len(line_noise_idx) > 0:
                line_ratio = np.mean(psd[line_noise_idx]) / (np.mean(psd) + 1e-6)
                if line_ratio > th['line_noise_ratio']: is_ch_good = False
            
            if not is_ch_good: bad_channels_in_trial.append(ch)
            
        bad_ratio = len(bad_channels_in_trial) / num_channels
        is_good = bad_ratio <= th['bad_channel_ratio']
        return is_good

    def extract_hjorth_parameters(self, x):
        activity = np.var(x)
        dx = np.diff(x)
        mobility = np.std(dx) / (np.std(x) + 1e-6)
        ddx = np.diff(dx)
        complexity = (np.std(ddx) / (np.std(dx) + 1e-6)) / (mobility + 1e-6)
        return activity, mobility, complexity

    def process_and_extract(self, X):
        X = self._bandpass_filter(X, lowcut=2.0, highcut=45.0)
        X_good = X[:, self.good_channels, :]
        
        start_idx = int(2.0 * self.fs)
        end_idx = int(4.0 * self.fs)
        X_sliced = X_good[:, :, start_idx:end_idx] if X_good.shape[2] >= end_idx else X_good[:, :, start_idx:]
        
        num_trials, num_channels, num_samples = X_sliced.shape
        all_features =[]
        channel_pairs = list(itertools.combinations(range(num_channels), 2))

        for trial_idx in range(num_trials):
            trial_data = X_sliced[trial_idx]
            trial_features =[]

            # 1. 频域
            nperseg = min(self.fs, num_samples)
            freqs, psd = welch(trial_data, fs=self.fs, axis=-1, nperseg=nperseg)
            bands = {'theta': (4, 8), 'alpha': (8, 13), 'beta': (13, 30), 'gamma': (30, 45)}
            for band_name, (fmin, fmax) in bands.items():
                idx = np.logical_and(freqs >= fmin, freqs <= fmax)
                trial_features.extend(np.mean(psd[:, idx], axis=-1))

            # 2. 时域
            for ch in range(num_channels):
                trial_features.extend(self.extract_hjorth_parameters(trial_data[ch]))

            # 3. 相干性
            for ch1, ch2 in channel_pairs:
                f_coh, Cxy = coherence(trial_data[ch1], trial_data[ch2], fs=self.fs, nperseg=nperseg)
                alpha_idx = np.logical_and(f_coh >= 8, f_coh <= 13)
                beta_idx = np.logical_and(f_coh >= 13, f_coh <= 30)
                trial_features.extend([np.mean(Cxy[alpha_idx]), np.mean(Cxy[beta_idx])])

            all_features.append(trial_features)

        return np.real(np.array(all_features)).astype(float)


# =====================================================================
# ================= 视觉刺激与闭环主程序 (兼容模型预测) ===============
# =====================================================================

def run_paradigm(mode='calibration', model=None, analyzer=None, save_filename="data_online.npy"):
    """
    mode: 
      - 'calibration': 仅使用阈值算法，用于收集训练数据
      - 'test': 使用传入的机器学习模型进行分类预测
    """
    with open("1.txt", "w") as f:
        f.write("")

    win = visual.Window(fullscr=True, size=(1500,1000), color=(0, 0, 0), units="pix")

    # 视觉元素
    hand_open = visual.ImageStim(win, image='hand_open.png', size=(600, 300), pos=(0, -250))
    hand_close = visual.ImageStim(win, image='hand_close.png', size=(600, 300), pos=(0, -250))
    ball_white = visual.ImageStim(win, image='white.png', mask='circle', size=(150, 150))
    ball_black = visual.ImageStim(win, image='black.png', mask='circle', size=(150, 150))

    prompt_text = visual.TextBox2(win, text="", letterHeight=40, pos=(0, 250), color=(1, 1, 1), alignment='center')
    feedback_text = visual.TextStim(win, text="", pos=(0, 0), color='white', height=40)

    Y_START = 350
    Y_END = -200 

    data_all =[] 
    labels_all =[]

    # --- 生成条件列表 ---
    num_real = NUM_TRIALS // 2
    num_blank = NUM_TRIALS - num_real
    condition_list = [True] * num_real + [False] * num_blank
    np.random.shuffle(condition_list)
    
    for trial in range(NUM_TRIALS):
        is_real_trial = condition_list[trial]
        
        # 1. 准备阶段
        if is_real_trial:
            prompt_text.text = f"Trial {trial+1}/{NUM_TRIALS}\nRelax and wait for the ball"
            for _ in range(60): 
                prompt_text.draw()
                hand_open.draw() 
                win.flip()
        else:
            for _ in range(60): 
                win.flip()
            
        # 2. 打Marker
        with open("1.txt", "a") as f:
            f.write("marker\n")
            
        # 3. 刺激核心循环
        for frameN in range(TOTAL_FRAMES):
            if is_real_trial:
                current_y = Y_START - ((Y_START - Y_END) * (frameN / TOTAL_FRAMES))
                ball_white.pos = (0, current_y)
                ball_black.pos = (0, current_y)
                
                hand_open.draw() 
                
                if frameN < FRAMES_REST:
                    ball_white.draw() 
                else:
                    mi_idx = frameN - FRAMES_REST
                    if m_mi_sequence[mi_idx] == 1:
                        ball_white.draw()
                    else:
                        ball_black.draw()
            win.flip()
            
        # ================= 在线计算 =================
        core.wait(0.1) 
        trial_data = read_latest_trial()
        
        show_hand = None
        if trial_data is not None:
            data_all.append(trial_data)
            labels_all.append("Real" if is_real_trial else "Control")
            
            # 【重要】：无论何种模式，都运行原有的阈值算法，以保留你想要的 ERS 和 Coh 显示值
            is_mi_algo, val_ers, val_coh = analyze_mi_trial(trial_data, fs=FS)
            
            # --- 核心判断逻辑切分 ---
            if mode == 'calibration':
                # 收集数据阶段：使用原本的阈值判定
                is_mi = is_mi_algo
            elif mode == 'test' and model is not None and analyzer is not None:
                # 测试预测阶段：使用机器学习模型判定
                is_good = analyzer.check_signal_quality(trial_data)
                if is_good:
                    X_trial = np.expand_dims(trial_data, axis=0) # 扩增维度以适配分析器 (1, channels, time)
                    features = analyzer.process_and_extract(X_trial)
                    pred = model.predict(features)[0]
                    is_mi = (pred == "Real") # 预测为 Real 即认为发生了运动想象
                else:
                    is_mi = False # 信号质量差，直接判定为否
            
            # --- 终端打印记录 ---
            trial_type = "Real" if is_real_trial else "Control"
            print(f"[{mode.upper()} - Trial {trial+1}] Type: {trial_type} | MI Pass: {is_mi} | ERS: {val_ers:.1f}% | Coh: {val_coh:.3f}")
            
            # --- 设置屏幕文字和手势 ---
            if is_mi:
                if is_real_trial:
                    feedback_text.text = f"SUCCESS: Hand Grasped!\nERS: {val_ers:.1f}% | Coh: {val_coh:.3f}"
                    feedback_text.color = 'green'
                else:
                    feedback_text.text = f"Control (Condition Met)\nERS: {val_ers:.1f}% | Coh: {val_coh:.3f}"
                    feedback_text.color = 'white'
                show_hand = hand_close
            else:
                if is_real_trial:
                    feedback_text.text = f"FAILED: No Movement!\nERS: {val_ers:.1f}% | Coh: {val_coh:.3f}"
                    feedback_text.color = 'red'
                else:
                    feedback_text.text = f"Control (Condition Not Met)\nERS: {val_ers:.1f}% | Coh: {val_coh:.3f}"
                    feedback_text.color = 'white'
                show_hand = hand_open
                
        else:
            print(f"[Trial {trial+1}] Type: {'Real' if is_real_trial else 'Control'} | DATA ERROR")
            feedback_text.text = "DATA ERROR: Please check connection"
            feedback_text.color = 'yellow'

        # 4. 动态结果反馈展现
        for _ in range(300):
            if is_real_trial and (show_hand is not None):
                show_hand.draw() 
            feedback_text.draw()
            win.flip()

        if 'escape' in event.getKeys():
            break

    # 保存当前Session数据
    save_dict = {"data": np.array(data_all, dtype=object), "labels": np.array(labels_all)}
    np.save(save_filename, save_dict)
    win.close()
    
    return np.array(data_all, dtype=object), np.array(labels_all)

# =====================================================================
# ================= 主控制流 (按顺序执行你的三个需求) =================
# =====================================================================
if __name__ == "__main__":
    
    SUBJECT = "online_test"
    
    # 实例化特征提取分析器
    analyzer = AdvancedCrossSessionMIAnalyzer(
        subject=SUBJECT,
        fs=FS,
        enable_quality_filter=True,
        quality_threshold={
            'amplitude_max': 800, 'amplitude_min': 1.0, 'variance_min': 5,
            'variance_max': 3000, 'line_noise_ratio': 25, 'kurtosis_max': 8, 'bad_channel_ratio': 0.5
        }
    )

    # ---------------- 阶段 1: 收集校准/训练数据 ----------------
    print("\n" + "="*40)
    print(" 阶段 1: 开始收集训练数据 (Calibration)")
    print("="*40)
    # 这一步使用你的原有算法给受试者反馈
    train_data, train_labels = run_paradigm(mode='calibration', save_filename=f"data_{SUBJECT}_train.npy")

    # ---------------- 阶段 2: 提取特征并训练模型 ----------------
    print("\n" + "="*40)
    print(" 阶段 2: 正在清洗数据并训练 SVM 机器学习模型...")
    print("="*40)
    
    # 过滤出质量合格的 Trial 用于训练
    X_train_filtered, y_train_filtered = [],[]
    for i in range(len(train_data)):
        if analyzer.check_signal_quality(train_data[i]):
            X_train_filtered.append(train_data[i])
            y_train_filtered.append(train_labels[i])
            
    if len(X_train_filtered) < 2:
        print("❌ 错误：有效训练数据太少，请重新运行收集数据阶段！")
        core.quit()

    X_train_arr = np.stack(X_train_filtered).astype(float)
    y_train_arr = np.array(y_train_filtered)
    
    # 提取特征
    print(f"提取特征中... (保留了 {len(y_train_arr)} 个有效 Trial)")
    X_train_features = analyzer.process_and_extract(X_train_arr)
    
    # 构建你的 Pipeline 和 GridSearch 逻辑
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('feature_selection', SelectKBest(score_func=f_classif)), 
        ('svm', SVC(kernel='rbf', random_state=42, class_weight='balanced'))
    ])
    
    # 这里 k 的上限做了动态处理，防止选的特征数超出总特征数或样本数导致报错
    max_k = min(80, X_train_features.shape[1])
    param_grid = {
        'feature_selection__k': [10, 20, max_k, 'all'] if max_k > 20 else [10, 'all'],
        'svm__C':[0.1, 1, 10],
        'svm__gamma':['scale', 'auto', 0.01]
    }
    
    grid_search = GridSearchCV(pipeline, param_grid, cv=min(3, len(y_train_arr)//2), scoring='accuracy')
    grid_search.fit(X_train_features, y_train_arr)
    best_model = grid_search.best_estimator_
    print("✅ 模型训练完成！")

    # ---------------- 阶段 3: 使用模型进行在线预测 ----------------
    print("\n" + "="*40)
    print(" 阶段 3: 开始在线测试 (使用训练好的模型预测)")
    print("="*40)
    # 这时候 mode 变成了 test，不再使用硬性阈值，而是用上方的 best_model 实时算
    test_data, test_labels = run_paradigm(mode='test', model=best_model, analyzer=analyzer, save_filename=f"data_{SUBJECT}_test.npy")
    
    core.quit()