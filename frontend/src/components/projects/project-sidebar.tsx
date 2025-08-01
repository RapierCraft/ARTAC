'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Home, Compass, MoreVertical, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui/tooltip'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useProjectStore } from '@/stores/project-store'
import { CreateProjectDialog } from './create-project-dialog'
import { cn } from '@/lib/utils'

export function ProjectSidebar() {
  const { projects, activeProject, setActiveProject, deleteProject, initializeStore, loadProjects, isLoading } = useProjectStore()
  const [showCreateProject, setShowCreateProject] = useState(false)
  const [hoveredProject, setHoveredProject] = useState<string | null>(null)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null)

  // Initialize the project store on mount
  useEffect(() => {
    initializeStore()
  }, [initializeStore])

  // Delete project handlers
  const handleDeleteProject = (projectId: string) => {
    setProjectToDelete(projectId)
    setShowDeleteDialog(true)
  }

  const confirmDeleteProject = () => {
    if (projectToDelete) {
      deleteProject(projectToDelete)
      setProjectToDelete(null)
    }
    setShowDeleteDialog(false)
  }

  const cancelDeleteProject = () => {
    setProjectToDelete(null)
    setShowDeleteDialog(false)
  }

  // Removed aggressive polling - projects don't change frequently enough to justify this

  return (
    <TooltipProvider>
      <div className="w-14 bg-card border-r border-border flex flex-col items-center py-3 space-y-2">
        {/* Home Button */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "w-8 h-8 rounded-2xl bg-muted hover:bg-primary hover:rounded-xl transition-all duration-200 p-0",
                !activeProject && "bg-primary rounded-xl"
              )}
              onClick={() => setActiveProject(null)}
            >
              <Home className={cn(
                "h-3.5 w-3.5",
                !activeProject ? "text-primary-foreground" : "text-foreground"
              )} />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <div>
              <p className="font-semibold">ARTAC Home</p>
              <p className="text-xs text-muted-foreground">Base organization with CEO & core channels</p>
            </div>
          </TooltipContent>
        </Tooltip>

        {/* Divider */}
        <div className="w-8 h-0.5 bg-border rounded-full" />

        {/* Projects List */}
        <ScrollArea className="flex-1 w-full">
          <div className="flex flex-col items-center space-y-2 px-3">
            {projects.map((project) => (
              <motion.div
                key={project.id}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="relative group"
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className={cn(
                        "w-8 h-8 rounded-2xl hover:rounded-xl transition-all duration-200 p-0 relative",
                        activeProject === project.id 
                          ? "rounded-xl" 
                          : "hover:rounded-xl"
                      )}
                      style={{
                        backgroundColor: activeProject === project.id 
                          ? project.color || '#3b82f6'
                          : hoveredProject === project.id 
                            ? project.color || '#3b82f6'
                            : 'hsl(var(--muted))'
                      }}
                      onClick={() => setActiveProject(project.id)}
                      onMouseEnter={() => setHoveredProject(project.id)}
                      onMouseLeave={() => setHoveredProject(null)}
                    >
                      {project.icon ? (
                        <span className="text-lg">{project.icon}</span>
                      ) : (
                        <div className="w-full h-full rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-primary-foreground font-bold text-sm">
                          {project.name.charAt(0).toUpperCase()}
                        </div>
                      )}
                      
                      {/* Active Indicator */}
                      {activeProject === project.id && (
                        <motion.div
                          layoutId="activeProject"
                          className="absolute -left-1 top-1/2 transform -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full"
                          transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        />
                      )}
                      
                      {/* Notification Badge */}
                      {project.id === 'project-artac' && (
                        <div className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-destructive rounded-full flex items-center justify-center">
                          <span className="text-xs text-destructive-foreground font-bold">3</span>
                        </div>
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <div>
                      <p className="font-semibold">{project.name}</p>
                      {project.description && (
                        <p className="text-xs text-muted-foreground">{project.description}</p>
                      )}
                    </div>
                  </TooltipContent>
                </Tooltip>

                {/* Three Dots Menu - Only show on hover */}
                <div className="absolute -top-1 -right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-4 h-4 p-0 bg-background border border-border rounded-full shadow-sm hover:bg-muted"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="h-2.5 w-2.5" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" side="right">
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteProject(project.id)
                        }}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete Project
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </motion.div>
            ))}
          </div>
        </ScrollArea>

        {/* Add Project Button */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="w-8 h-8 rounded-2xl bg-muted hover:bg-primary hover:rounded-xl transition-all duration-200 p-0 group"
              onClick={() => setShowCreateProject(true)}
            >
              <Plus className="h-4 w-4 text-muted-foreground group-hover:text-primary-foreground transition-colors" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Add Project</p>
          </TooltipContent>
        </Tooltip>

        {/* Explore Projects */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="w-8 h-8 rounded-2xl bg-muted hover:bg-primary hover:rounded-xl transition-all duration-200 p-0 group"
            >
              <Compass className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary-foreground transition-colors" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Explore Public Projects</p>
          </TooltipContent>
        </Tooltip>

        {/* Create Project Dialog */}
        <CreateProjectDialog
          open={showCreateProject}
          onOpenChange={setShowCreateProject}
        />

        {/* Delete Project Confirmation Dialog */}
        <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Project</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete this project? This action cannot be undone and will remove all project data, channels, and messages.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={cancelDeleteProject}>Cancel</AlertDialogCancel>
              <AlertDialogAction 
                onClick={confirmDeleteProject}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Delete Project
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </TooltipProvider>
  )
}