'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ArrowLeft, 
  Upload, 
  Camera, 
  Palette, 
  Users, 
  Globe, 
  Lock,
  Check,
  X,
  Sparkles,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { useProjectStore } from '@/stores/project-store'
import { cn } from '@/lib/utils'

interface CreateProjectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

type Step = 'template' | 'customize' | 'settings' | 'invite' | 'complete'

const predefinedColors = [
  '#3b82f6', '#8b5cf6', '#ef4444', '#f59e0b', '#10b981', 
  '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#64748b'
]

const predefinedIcons = [
  '🚀', '🎮', '📚', '💼', '🎨', '🔬', '🎵', '🏠', '🌟', '⚡',
  '🎯', '🔥', '💎', '🌈', '🎪', '🎭', '🎲', '🎸', '🎬', '📱'
]

export function CreateProjectDialog({ open, onOpenChange }: CreateProjectDialogProps) {
  const { createProject, createFromTemplate, getTemplates } = useProjectStore()
  const [step, setStep] = useState<Step>('template')
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  
  // Project data
  const [projectName, setProjectName] = useState('')
  const [projectDescription, setProjectDescription] = useState('')
  const [projectIcon, setProjectIcon] = useState('🚀')
  const [projectColor, setProjectColor] = useState('#3b82f6')
  const [projectBanner, setProjectBanner] = useState<string | null>(null)
  
  // Settings
  const [isPublic, setIsPublic] = useState(false)
  const [allowInvites, setAllowInvites] = useState(true)
  const [verificationLevel, setVerificationLevel] = useState<'none' | 'low' | 'medium' | 'high'>('low')
  const [defaultNotifications, setDefaultNotifications] = useState(true)

  const templates = getTemplates()

  const handleNext = () => {
    if (step === 'template') {
      setStep('customize')
    } else if (step === 'customize') {
      setStep('settings')
    } else if (step === 'settings') {
      setStep('invite')
    } else if (step === 'invite') {
      handleCreateProject()
    }
  }

  const handleBack = () => {
    if (step === 'customize') {
      setStep('template')
    } else if (step === 'settings') {
      setStep('customize')
    } else if (step === 'invite') {
      setStep('settings')
    }
  }

  const handleCreateProject = () => {
    if (selectedTemplate) {
      createFromTemplate(selectedTemplate, projectName)
    } else {
      createProject({
        name: projectName,
        description: projectDescription,
        icon: projectIcon,
        color: projectColor,
        banner: projectBanner,
        isActive: true,
        owner: 'current-user',
        members: ['current-user'],
        channels: [],
        settings: {
          isPublic,
          allowInvites,
          defaultNotifications,
          verificationLevel,
          explicitContentFilter: 'members_without_roles',
          defaultMessageNotifications: 'only_mentions',
          systemChannelFlags: []
        }
      })
    }
    
    setStep('complete')
    setTimeout(() => {
      onOpenChange(false)
      resetForm()
    }, 2000)
  }

  const resetForm = () => {
    setStep('template')
    setSelectedTemplate(null)
    setProjectName('')
    setProjectDescription('')
    setProjectIcon('🚀')
    setProjectColor('#3b82f6')
    setProjectBanner(null)
    setIsPublic(false)
    setAllowInvites(true)
    setVerificationLevel('low')
    setDefaultNotifications(true)
  }

  const stepVariants = {
    hidden: { opacity: 0, x: 20 },
    visible: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl h-[80vh] p-0">
        <div className="flex h-full">
          {/* Progress Sidebar */}
          <div className="w-64 bg-muted p-6 border-r border-border">
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <span className="font-semibold">Create Project</span>
              </div>
              
              <div className="space-y-3">
                {[
                  { id: 'template', label: 'Choose Template', icon: '📋' },
                  { id: 'customize', label: 'Customize', icon: '🎨' },
                  { id: 'settings', label: 'Settings', icon: '⚙️' },
                  { id: 'invite', label: 'Invite & Launch', icon: '🚀' }
                ].map((s, index) => (
                  <div
                    key={s.id}
                    className={cn(
                      "flex items-center space-x-3 p-2 rounded-lg transition-colors",
                      step === s.id && "bg-accent text-accent-foreground",
                      (step === 'customize' && index < 1) ||
                      (step === 'settings' && index < 2) ||
                      (step === 'invite' && index < 3) ||
                      (step === 'complete' && index < 4)
                        ? "text-primary" 
                        : step !== s.id && "text-muted-foreground"
                    )}
                  >
                    <span className="text-lg">{s.icon}</span>
                    <span className="text-sm font-medium">{s.label}</span>
                    {((step === 'customize' && index < 1) ||
                      (step === 'settings' && index < 2) ||
                      (step === 'invite' && index < 3) ||
                      (step === 'complete' && index < 4)) && (
                      <Check className="h-4 w-4 ml-auto" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 flex flex-col">
            <DialogHeader className="p-6 border-b">
              <div className="flex items-center justify-between">
                {step !== 'template' && step !== 'complete' && (
                  <Button variant="ghost" size="sm" onClick={handleBack}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back
                  </Button>
                )}
                {step === 'complete' && (
                  <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </DialogHeader>

            <ScrollArea className="flex-1">
              <div className="p-6">
                <AnimatePresence mode="wait">
                  {/* Template Selection */}
                  {step === 'template' && (
                    <motion.div
                      key="template"
                      variants={stepVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      className="space-y-6"
                    >
                      <div>
                        <DialogTitle className="text-2xl font-bold mb-2">
                          Choose a template
                        </DialogTitle>
                        <p className="text-muted-foreground">
                          Start with a template or create from scratch
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        {/* Custom Template */}
                        <div
                          className={cn(
                            "p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-primary",
                            selectedTemplate === null && "border-primary bg-primary/5"
                          )}
                          onClick={() => setSelectedTemplate(null)}
                        >
                          <div className="text-center space-y-2">
                            <div className="text-4xl">🎯</div>
                            <h3 className="font-semibold">Create My Own</h3>
                            <p className="text-sm text-muted-foreground">
                              Start from scratch with full customization
                            </p>
                          </div>
                        </div>

                        {/* Template Options */}
                        {templates.map((template) => (
                          <div
                            key={template.id}
                            className={cn(
                              "p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-primary",
                              selectedTemplate === template.id && "border-primary bg-primary/5"
                            )}
                            onClick={() => setSelectedTemplate(template.id)}
                          >
                            <div className="text-center space-y-2">
                              <div className="text-4xl">{template.icon}</div>
                              <h3 className="font-semibold">{template.name}</h3>
                              <p className="text-sm text-muted-foreground">
                                {template.description}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {/* Customization */}
                  {step === 'customize' && (
                    <motion.div
                      key="customize"
                      variants={stepVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      className="space-y-6"
                    >
                      <div>
                        <DialogTitle className="text-2xl font-bold mb-2">
                          Customize your project
                        </DialogTitle>
                        <p className="text-muted-foreground">
                          Give your project a name and personality
                        </p>
                      </div>

                      {/* Project Preview */}
                      <div className="bg-card border border-border rounded-lg p-4 text-card-foreground">
                        <div className="flex items-center space-x-3">
                          <div 
                            className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl"
                            style={{ backgroundColor: projectColor }}
                          >
                            {projectIcon}
                          </div>
                          <div>
                            <h3 className="font-semibold">
                              {projectName || 'My Awesome Project'}
                            </h3>
                            <p className="text-sm text-muted-foreground">
                              {projectDescription || 'A great place to collaborate'}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        {/* Project Name */}
                        <div>
                          <Label htmlFor="name">Project Name *</Label>
                          <Input
                            id="name"
                            value={projectName}
                            onChange={(e) => setProjectName(e.target.value)}
                            placeholder="Enter project name"
                            className="mt-1"
                          />
                        </div>

                        {/* Project Description */}
                        <div>
                          <Label htmlFor="description">Description</Label>
                          <Textarea
                            id="description"
                            value={projectDescription}
                            onChange={(e) => setProjectDescription(e.target.value)}
                            placeholder="What's this project about?"
                            className="mt-1"
                            rows={3}
                          />
                        </div>

                        {/* Icon Selection */}
                        <div>
                          <Label>Project Icon</Label>
                          <div className="grid grid-cols-10 gap-2 mt-2">
                            {predefinedIcons.map((icon) => (
                              <button
                                key={icon}
                                className={cn(
                                  "w-10 h-10 rounded-lg border-2 flex items-center justify-center text-xl transition-all",
                                  projectIcon === icon 
                                    ? "border-primary bg-accent" 
                                    : "border-border hover:border-primary"
                                )}
                                onClick={() => setProjectIcon(icon)}
                              >
                                {icon}
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Color Selection */}
                        <div>
                          <Label>Project Color</Label>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {predefinedColors.map((color) => (
                              <button
                                key={color}
                                className={cn(
                                  "w-8 h-8 rounded-full border-2 transition-all",
                                  projectColor === color 
                                    ? "border-foreground scale-110" 
                                    : "border-border hover:scale-105"
                                )}
                                style={{ backgroundColor: color }}
                                onClick={() => setProjectColor(color)}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Settings */}
                  {step === 'settings' && (
                    <motion.div
                      key="settings"
                      variants={stepVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      className="space-y-6"
                    >
                      <div>
                        <DialogTitle className="text-2xl font-bold mb-2">
                          Project Settings
                        </DialogTitle>
                        <p className="text-muted-foreground">
                          Configure privacy and security settings
                        </p>
                      </div>

                      <div className="space-y-6">
                        {/* Privacy Settings */}
                        <div className="space-y-4">
                          <h3 className="font-semibold flex items-center">
                            <Lock className="h-4 w-4 mr-2" />
                            Privacy
                          </h3>
                          
                          <div className="flex items-center justify-between p-4 border rounded-lg">
                            <div>
                              <div className="font-medium">Public Project</div>
                              <div className="text-sm text-muted-foreground">
                                Anyone can find and join this project
                              </div>
                            </div>
                            <Switch checked={isPublic} onCheckedChange={setIsPublic} />
                          </div>

                          <div className="flex items-center justify-between p-4 border rounded-lg">
                            <div>
                              <div className="font-medium">Allow Invites</div>
                              <div className="text-sm text-muted-foreground">
                                Members can invite others to join
                              </div>
                            </div>
                            <Switch checked={allowInvites} onCheckedChange={setAllowInvites} />
                          </div>
                        </div>

                        {/* Security Settings */}
                        <div className="space-y-4">
                          <h3 className="font-semibold flex items-center">
                            <Users className="h-4 w-4 mr-2" />
                            Verification Level
                          </h3>
                          
                          <Select value={verificationLevel} onValueChange={(value: any) => setVerificationLevel(value)}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">None - No verification required</SelectItem>
                              <SelectItem value="low">Low - Email verification required</SelectItem>
                              <SelectItem value="medium">Medium - Registered account (5+ minutes)</SelectItem>
                              <SelectItem value="high">High - Verified phone number</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Notification Settings */}
                        <div className="space-y-4">
                          <h3 className="font-semibold">Notifications</h3>
                          
                          <div className="flex items-center justify-between p-4 border rounded-lg">
                            <div>
                              <div className="font-medium">Default Notifications</div>
                              <div className="text-sm text-muted-foreground">
                                Enable notifications for new members
                              </div>
                            </div>
                            <Switch checked={defaultNotifications} onCheckedChange={setDefaultNotifications} />
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Invite & Launch */}
                  {step === 'invite' && (
                    <motion.div
                      key="invite"
                      variants={stepVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      className="space-y-6"
                    >
                      <div>
                        <DialogTitle className="text-2xl font-bold mb-2">
                          Ready to launch!
                        </DialogTitle>
                        <p className="text-muted-foreground">
                          Your project is ready. You can invite people later.
                        </p>
                      </div>

                      {/* Project Summary */}
                      <div className="bg-muted rounded-lg p-6 space-y-4">
                        <div className="flex items-center space-x-4">
                          <div 
                            className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl"
                            style={{ backgroundColor: projectColor }}
                          >
                            {projectIcon}
                          </div>
                          <div>
                            <h3 className="text-xl font-bold">{projectName}</h3>
                            <p className="text-muted-foreground">{projectDescription}</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div className="flex items-center space-x-2">
                            <Globe className="h-4 w-4" />
                            <span>{isPublic ? 'Public' : 'Private'}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Users className="h-4 w-4" />
                            <span>Invites {allowInvites ? 'Enabled' : 'Disabled'}</span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Complete */}
                  {step === 'complete' && (
                    <motion.div
                      key="complete"
                      variants={stepVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      className="text-center space-y-6 py-12"
                    >
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2 }}
                        className="w-20 h-20 bg-accent rounded-full flex items-center justify-center mx-auto"
                      >
                        <Check className="h-10 w-10 text-primary" />
                      </motion.div>
                      
                      <div>
                        <h2 className="text-2xl font-bold text-primary mb-2">
                          Project Created!
                        </h2>
                        <p className="text-muted-foreground">
                          {projectName} is ready to go. Welcome to your new project!
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </ScrollArea>

            {/* Footer */}
            {step !== 'complete' && (
              <div className="p-6 border-t border-border bg-muted/50">
                <div className="flex justify-end space-x-3">
                  <Button variant="outline" onClick={() => onOpenChange(false)}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleNext}
                    disabled={step === 'customize' && !projectName.trim()}
                  >
                    {step === 'invite' ? (
                      <>
                        <Zap className="h-4 w-4 mr-2" />
                        Create Project
                      </>
                    ) : (
                      'Next'
                    )}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}