import { useTranslation } from 'react-i18next';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Button } from '../ui/button';
import { Volume2 } from 'lucide-react';
import { useTTSStore, type TTSProvider } from '../../stores/tts-store';
import { SettingsSection } from './SettingsSection';

interface TTSControlsProps {
  className?: string;
}

/**
 * TTS Controls component for Settings
 * - Toggle TTS on/off
 * - Select provider (Piper, macOS, System)
 * - Select voice
 * - Test voice button
 */
export function TTSControls({ className }: TTSControlsProps) {
  const { t } = useTranslation('analytics');
  const {
    enabled,
    provider,
    selectedVoice,
    availableVoices,
    isLoading,
    isTesting,
    setEnabled,
    setProvider,
    setSelectedVoice,
    testVoice,
  } = useTTSStore();

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider as TTSProvider);
  };

  const handleVoiceChange = (voiceId: string) => {
    setSelectedVoice(voiceId);
  };

  const handleTestVoice = async () => {
    await testVoice();
  };

  const getProviderLabel = (providerKey: TTSProvider): string => {
    return t(`tts.providers.${providerKey}`);
  };

  return (
    <SettingsSection
      title={t('tts.title')}
      description=""
      className={className}
    >
      <div className="space-y-6">
        {/* Enable TTS Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="tts-enabled">{t('tts.enabled')}</Label>
            <p className="text-sm text-muted-foreground">{t('tts.enabledDescription')}</p>
          </div>
          <Switch
            id="tts-enabled"
            checked={enabled}
            onCheckedChange={setEnabled}
          />
        </div>

        {/* Provider Selection */}
        {enabled && (
          <>
            <div className="space-y-2">
              <Label htmlFor="tts-provider">{t('tts.provider')}</Label>
              <p className="text-sm text-muted-foreground mb-2">
                {t('tts.providerDescription')}
              </p>
              <Select value={provider} onValueChange={handleProviderChange}>
                <SelectTrigger id="tts-provider">
                  <SelectValue placeholder={t('tts.provider')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="piper">{getProviderLabel('piper')}</SelectItem>
                  <SelectItem value="macos">{getProviderLabel('macos')}</SelectItem>
                  <SelectItem value="system">{getProviderLabel('system')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Voice Selection */}
            <div className="space-y-2">
              <Label htmlFor="tts-voice">{t('tts.voice')}</Label>
              <p className="text-sm text-muted-foreground mb-2">
                {t('tts.voiceDescription')}
              </p>
              <Select
                value={selectedVoice || ''}
                onValueChange={handleVoiceChange}
                disabled={isLoading || availableVoices.length === 0}
              >
                <SelectTrigger id="tts-voice">
                  <SelectValue
                    placeholder={
                      isLoading
                        ? t('common:labels.loading')
                        : availableVoices.length === 0
                        ? t('tts.noVoicesAvailable')
                        : t('tts.selectVoice')
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {availableVoices.map((voice) => (
                    <SelectItem key={voice.id} value={voice.id}>
                      {voice.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Test Voice Button */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleTestVoice}
                disabled={!selectedVoice || isTesting}
              >
                <Volume2 className="h-4 w-4 mr-2" />
                {isTesting ? t('tts.testing') : t('tts.testVoice')}
              </Button>
            </div>
          </>
        )}
      </div>
    </SettingsSection>
  );
}
