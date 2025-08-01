'use client'

import { useState, useEffect } from 'react'
import { 
  Settings, 
  Bell, 
  Palette, 
  MessageSquare, 
  Shield, 
  User,
  Volume2,
  Monitor,
  CheckCircle,
  X
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { useNotificationStore } from '@/stores/notification-store'
import { useCommunicationStore } from '@/stores/communication-store'
import { Badge } from '@/components/ui/badge'

export function SettingsPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('notifications')
  const [isClient, setIsClient] = useState(false)
  
  const { 
    settings, 
    updateSettings, 
    checkNotificationPermission, 
    requestNotificationPermission 
  } = useNotificationStore()
  
  const { channels } = useCommunicationStore()

  useEffect(() => {
    setIsClient(true)
  }, [])

  const tabs = [
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'communication', label: 'Communication', icon: MessageSquare },
    { id: 'privacy', label: 'Privacy & Security', icon: Shield },
    { id: 'profile', label: 'Profile', icon: User }
  ]

  const handleNotificationPermission = async () => {
    if (isClient) {
      await requestNotificationPermission()
    }
  }

  const hasNotificationPermission = isClient && checkNotificationPermission() === 'granted'

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground hover:text-foreground"
        >
          <Settings className="h-5 w-5" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl h-[80vh] p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Settings
          </DialogTitle>
        </DialogHeader>
        
        <div className="flex h-full">
          {/* Sidebar */}
          <div className="w-64 border-r bg-muted/30 p-4">
            <div className="space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <Button
                    key={tab.id}
                    variant={activeTab === tab.id ? "secondary" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => setActiveTab(tab.id)}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.label}
                  </Button>
                )
              })}
            </div>
          </div>
          
          {/* Content */}
          <div className="flex-1">
            <ScrollArea className="h-full">
              <div className="p-6">
                {/* Notifications Tab */}
                {activeTab === 'notifications' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Notification Settings</h3>
                      
                      {/* Desktop Notifications Permission */}
                      <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg mb-4">
                        <div className="flex items-center gap-3">
                          <Monitor className="h-5 w-5" />
                          <div>
                            <p className="font-medium">Desktop Notifications</p>
                            <p className="text-sm text-muted-foreground">
                              Allow ARTAC to show desktop notifications
                            </p>
                          </div>
                        </div>
                        {hasNotificationPermission ? (
                          <Badge variant="secondary" className="bg-green-500/20 text-green-300">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Enabled
                          </Badge>
                        ) : (
                          <Button size="sm" onClick={handleNotificationPermission}>
                            Enable
                          </Button>
                        )}
                      </div>

                      {/* General Notification Settings */}
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Direct Messages</p>
                            <p className="text-sm text-muted-foreground">Notifications for DMs</p>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <Volume2 className="h-4 w-4" />
                              <Switch
                                checked={settings.directMessages.sound}
                                onCheckedChange={(checked) => 
                                  updateSettings({
                                    directMessages: { ...settings.directMessages, sound: checked }
                                  })
                                }
                              />
                            </div>
                            <div className="flex items-center gap-2">
                              <Monitor className="h-4 w-4" />
                              <Switch
                                checked={settings.directMessages.desktop}
                                onCheckedChange={(checked) => 
                                  updateSettings({
                                    directMessages: { ...settings.directMessages, desktop: checked }
                                  })
                                }
                              />
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Mentions & Replies</p>
                            <p className="text-sm text-muted-foreground">When you're mentioned or replied to</p>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <Volume2 className="h-4 w-4" />
                              <Switch
                                checked={settings.mentions.sound}
                                onCheckedChange={(checked) => 
                                  updateSettings({
                                    mentions: { ...settings.mentions, sound: checked }
                                  })
                                }
                              />
                            </div>
                            <div className="flex items-center gap-2">
                              <Monitor className="h-4 w-4" />
                              <Switch
                                checked={settings.mentions.desktop}
                                onCheckedChange={(checked) => 
                                  updateSettings({
                                    mentions: { ...settings.mentions, desktop: checked }
                                  })
                                }
                              />
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Memos</p>
                            <p className="text-sm text-muted-foreground">System memos and announcements</p>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <Volume2 className="h-4 w-4" />
                              <Switch
                                checked={settings.memos.sound}
                                onCheckedChange={(checked) => 
                                  updateSettings({
                                    memos: { ...settings.memos, sound: checked }
                                  })
                                }
                              />
                            </div>
                            <div className="flex items-center gap-2">
                              <Monitor className="h-4 w-4" />
                              <Switch
                                checked={settings.memos.desktop}
                                onCheckedChange={(checked) => 
                                  updateSettings({
                                    memos: { ...settings.memos, desktop: checked }
                                  })
                                }
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      <Separator />

                      {/* Channel-specific Settings */}
                      <div>
                        <h4 className="font-medium mb-4">Channel Notifications</h4>
                        <div className="space-y-3">
                          {channels.map((channel) => (
                            <div key={channel.id} className="flex items-center justify-between p-3 border rounded-lg">
                              <div>
                                <p className="font-medium">#{channel.name}</p>
                                <p className="text-sm text-muted-foreground">{channel.description}</p>
                              </div>
                              <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2">
                                  <Volume2 className="h-4 w-4" />
                                  <Switch
                                    checked={settings.channels[channel.id]?.sound ?? true}
                                    onCheckedChange={(checked) => 
                                      updateSettings({
                                        channels: {
                                          ...settings.channels,
                                          [channel.id]: {
                                            ...settings.channels[channel.id],
                                            sound: checked,
                                            desktop: settings.channels[channel.id]?.desktop ?? true,
                                            muted: settings.channels[channel.id]?.muted ?? false
                                          }
                                        }
                                      })
                                    }
                                  />
                                </div>
                                <div className="flex items-center gap-2">
                                  <Monitor className="h-4 w-4" />
                                  <Switch
                                    checked={settings.channels[channel.id]?.desktop ?? true}
                                    onCheckedChange={(checked) => 
                                      updateSettings({
                                        channels: {
                                          ...settings.channels,
                                          [channel.id]: {
                                            ...settings.channels[channel.id],
                                            desktop: checked,
                                            sound: settings.channels[channel.id]?.sound ?? true,
                                            muted: settings.channels[channel.id]?.muted ?? false
                                          }
                                        }
                                      })
                                    }
                                  />
                                </div>
                                <Button
                                  variant={settings.channels[channel.id]?.muted ? "destructive" : "outline"}
                                  size="sm"
                                  onClick={() => 
                                    updateSettings({
                                      channels: {
                                        ...settings.channels,
                                        [channel.id]: {
                                          ...settings.channels[channel.id],
                                          muted: !settings.channels[channel.id]?.muted,
                                          sound: settings.channels[channel.id]?.sound ?? true,
                                          desktop: settings.channels[channel.id]?.desktop ?? true
                                        }
                                      }
                                    })
                                  }
                                >
                                  {settings.channels[channel.id]?.muted ? "Unmute" : "Mute"}
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Appearance Tab */}
                {activeTab === 'appearance' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Appearance Settings</h3>
                      
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Theme</p>
                            <p className="text-sm text-muted-foreground">Choose your preferred theme</p>
                          </div>
                          <Select defaultValue="system">
                            <SelectTrigger className="w-32">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="light">Light</SelectItem>
                              <SelectItem value="dark">Dark</SelectItem>
                              <SelectItem value="system">System</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Compact Mode</p>
                            <p className="text-sm text-muted-foreground">Use smaller spacing and elements</p>
                          </div>
                          <Switch />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Show Animations</p>
                            <p className="text-sm text-muted-foreground">Enable UI animations and transitions</p>
                          </div>
                          <Switch defaultChecked />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Communication Tab */}
                {activeTab === 'communication' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Communication Preferences</h3>
                      
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Send Messages with Enter</p>
                            <p className="text-sm text-muted-foreground">Use Enter to send, Shift+Enter for new line</p>
                          </div>
                          <Switch defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Show Typing Indicators</p>
                            <p className="text-sm text-muted-foreground">Let others see when you're typing</p>
                          </div>
                          <Switch defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Auto-Mark as Read</p>
                            <p className="text-sm text-muted-foreground">Mark messages as read when viewed</p>
                          </div>
                          <Switch defaultChecked />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Privacy Tab */}
                {activeTab === 'privacy' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Privacy & Security</h3>
                      
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Show Online Status</p>
                            <p className="text-sm text-muted-foreground">Let others see when you're online</p>
                          </div>
                          <Switch defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Allow Direct Messages</p>
                            <p className="text-sm text-muted-foreground">Allow others to send you direct messages</p>
                          </div>
                          <Switch defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">Data Collection</p>
                            <p className="text-sm text-muted-foreground">Allow analytics and usage data collection</p>
                          </div>
                          <Switch />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Profile Tab */}
                {activeTab === 'profile' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Profile Settings</h3>
                      
                      <div className="space-y-4">
                        <div className="flex items-center gap-4">
                          <div className="h-16 w-16 rounded-full bg-primary flex items-center justify-center text-2xl font-bold">
                            U
                          </div>
                          <div>
                            <p className="font-medium">User Profile</p>
                            <p className="text-sm text-muted-foreground">Current user role and status</p>
                          </div>
                          <Button variant="outline" size="sm">
                            Change Avatar
                          </Button>
                        </div>

                        <div className="space-y-3">
                          <div>
                            <label className="text-sm font-medium">Status Message</label>
                            <Select defaultValue="online">
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="online">🟢 Online</SelectItem>
                                <SelectItem value="away">🟡 Away</SelectItem>
                                <SelectItem value="busy">🔴 Busy</SelectItem>
                                <SelectItem value="offline">⚫ Offline</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}