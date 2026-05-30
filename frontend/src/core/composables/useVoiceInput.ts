import { ref, computed } from 'vue'

/**
 * 语音输入 Composable
 * 
 * 利用 Web Speech API 实现语音转文字功能
 * 适用于工单内容快速录入、搜索等场景
 * 
 * @example
 * ```ts
 * const { isListening, transcript, startListening, stopListening } = useVoiceInput()
 * 
 * // 开始录音
 * startListening()
 * 
 * // 停止录音
 * stopListening()
 * 
 * // 获取转录文本
 * console.log(transcript.value)
 * ```
 */

export interface VoiceInputOptions {
  lang?: string          // 语言代码，默认 'zh-CN'
  continuous?: boolean   // 是否连续识别，默认 true
  interimResults?: boolean // 是否返回中间结果，默认 true
}

export function useVoiceInput(options: VoiceInputOptions = {}) {
  const {
    lang = 'zh-CN',
    continuous = true,
    interimResults = true,
  } = options
  
  const isListening = ref(false)
  const isSupported = ref(false)
  const transcript = ref('')
  const interimTranscript = ref('')
  const error = ref<string | null>(null)
  
  let recognition: any = null
  
  /**
   * 检测浏览器支持情况
   */
  function checkSupport(): boolean {
    const SpeechRecognition = (window as any).SpeechRecognition || 
                             (window as any).webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      console.warn('[VoiceInput] Web Speech API not supported in this browser')
      isSupported.value = false
      return false
    }
    
    isSupported.value = true
    return true
  }
  
  /**
   * 初始化语音识别
   */
  function initRecognition() {
    if (!checkSupport()) {
      return null
    }
    
    const SpeechRecognition = (window as any).SpeechRecognition || 
                             (window as any).webkitSpeechRecognition
    
    recognition = new SpeechRecognition()
    recognition.lang = lang
    recognition.continuous = continuous
    recognition.interimResults = interimResults
    
    // 识别结果
    recognition.onresult = (event: any) => {
      let finalTranscript = ''
      let interim = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const text = result[0].transcript
        
        if (result.isFinal) {
          finalTranscript += text
        } else {
          interim += text
        }
      }
      
      if (finalTranscript) {
        transcript.value += finalTranscript
      }
      
      interimTranscript.value = interim
    }
    
    // 识别错误
    recognition.onerror = (event: any) => {
      console.error('[VoiceInput] Recognition error:', event.error)
      
      switch (event.error) {
        case 'no-speech':
          error.value = '未检测到语音，请重试'
          break
        case 'audio-capture':
          error.value = '无法访问麦克风'
          break
        case 'not-allowed':
          error.value = '麦克风权限被拒绝'
          break
        case 'network':
          error.value = '网络连接错误'
          break
        default:
          error.value = `语音识别错误: ${event.error}`
      }
      
      isListening.value = false
    }
    
    // 识别开始
    recognition.onstart = () => {
      isListening.value = true
      error.value = null
      console.log('[VoiceInput] Started listening')
    }
    
    // 识别结束
    recognition.onend = () => {
      isListening.value = false
      console.log('[VoiceInput] Stopped listening')
    }
    
    return recognition
  }
  
  /**
   * 开始语音识别
   */
  function startListening() {
    if (!recognition) {
      initRecognition()
    }
    
    if (!recognition) {
      error.value = '您的浏览器不支持语音识别'
      return
    }
    
    if (isListening.value) {
      console.warn('[VoiceInput] Already listening')
      return
    }
    
    try {
      // 清空之前的转录
      transcript.value = ''
      interimTranscript.value = ''
      error.value = null
      
      recognition.start()
    } catch (err) {
      console.error('[VoiceInput] Failed to start:', err)
      error.value = '启动语音识别失败'
    }
  }
  
  /**
   * 停止语音识别
   */
  function stopListening() {
    if (recognition && isListening.value) {
      recognition.stop()
    }
  }
  
  /**
   * 取消语音识别
   */
  function cancelListening() {
    if (recognition) {
      recognition.abort()
      isListening.value = false
    }
  }
  
  /**
   * 清空转录结果
   */
  function clearTranscript() {
    transcript.value = ''
    interimTranscript.value = ''
  }
  
  /**
   * 追加到现有文本
   */
  function appendToText(existingText: string): string {
    return existingText + transcript.value
  }
  
  /**
   * 替换选中文本（用于编辑器集成）
   */
  function replaceSelection(
    text: string,
    selectionStart: number,
    selectionEnd: number
  ): string {
    return text.substring(0, selectionStart) + 
           transcript.value + 
           text.substring(selectionEnd)
  }
  
  // 初始化时检查支持情况
  checkSupport()
  
  return {
    isSupported,
    isListening,
    transcript,
    interimTranscript,
    fullTranscript: computed(() => transcript.value + interimTranscript.value),
    error,
    startListening,
    stopListening,
    cancelListening,
    clearTranscript,
    appendToText,
    replaceSelection,
  }
}

/**
 * 语音输入按钮组件配置
 */
export interface VoiceButtonConfig {
  label?: string
  listeningLabel?: string
  icon?: string
  listeningIcon?: string
}

export const defaultVoiceButtonConfig: VoiceButtonConfig = {
  label: '点击说话',
  listeningLabel: '正在聆听...',
  icon: '🎤',
  listeningIcon: '⏹️',
}
