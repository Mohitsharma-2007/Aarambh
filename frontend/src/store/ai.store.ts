import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/api'

interface AIModel {
  id: string
  name: string
}

interface AIProvider {
  id: string
  name: string
  models: AIModel[]
  available: boolean
}

interface AIState {
  providers: AIProvider[]
  selectedProvider: string
  selectedModel: string
  initialized: boolean
  setProvider: (provider: string) => void
  setModel: (model: string) => void
  fetchProviders: () => Promise<void>
}

export const useAIStore = create<AIState>()(
  persist(
    (set, get) => ({
      providers: [],
      selectedProvider: 'openrouter',
      selectedModel: 'meta-llama/llama-3.1-405b-instruct:free',
      initialized: false,
      
      setProvider: (providerId) => {
        set({ selectedProvider: providerId })
        // Auto-select first model of new provider if current model doesn't belong
        const provider = get().providers.find(p => p.id === providerId)
        if (provider && provider.models.length > 0) {
          const currentModel = get().selectedModel
          if (!provider.models.find(m => m.id === currentModel)) {
            set({ selectedModel: provider.models[0].id })
          }
        }
      },
      
      setModel: (model) => set({ selectedModel: model }),
      
      fetchProviders: async () => {
        try {
          const data = await api.getAIProviders()
          // Ensure providers is always an array
          const providers = data?.providers || []
          set({ providers, initialized: true })
          
          // Initial selection if none exists or invalid
          if (!get().selectedProvider && data?.default) {
            set({ selectedProvider: data.default })
          }
          
          // Validate current provider selection and auto-select first model if needed
          const currentProviderId = get().selectedProvider
          const currentModel = get().selectedModel
          const currentProvider = providers.find((p: any) => p.id === currentProviderId)
          
          if (currentProvider && currentProvider.models?.length > 0 && !currentModel) {
            set({ selectedModel: currentProvider.models[0].id })
          }
        } catch (err) {
          console.error('Failed to fetch AI providers:', err)
          // Ensure providers is at least an empty array on error
          set({ providers: [], initialized: true })
        }
      },
    }),
    {
      name: 'ai-settings-storage',
      partialize: (state) => ({ 
        selectedProvider: state.selectedProvider, 
        selectedModel: state.selectedModel 
      }),
    }
  )
)
