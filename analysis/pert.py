"""
analysis/pert.py — Módulo P12
PERT/CPM Planning — SincelejoRoute v2

Models the construction timeline of "Metro Sabanas Phase 2" (Intercambiadores).
Calculates Critical Path, Early Start, Late Start, and Slack time.
Generates an ASCII Gantt Chart.
"""

class Task:
    def __init__(self, name, duration, predecessors=None):
        self.name = name
        self.duration = duration
        self.predecessors = predecessors if predecessors else []
        self.es = 0  # Early Start
        self.ef = 0  # Early Finish
        self.ls = 0  # Late Start
        self.lf = 0  # Late Finish
        self.slack = 0

class PERTManager:
    def __init__(self):
        self.tasks = {}

    def add_task(self, name, duration, predecessors=None):
        self.tasks[name] = Task(name, duration, predecessors)

    def calculate(self):
        # Forward pass
        for name, task in self.tasks.items():
            if not task.predecessors:
                task.es = 0
            else:
                task.es = max(self.tasks[p].ef for p in task.predecessors)
            task.ef = task.es + task.duration

        total_time = max(t.ef for t in self.tasks.values())

        # Backward pass
        # Sort keys reverse to ensure we process successors first
        sorted_tasks = list(self.tasks.keys())[::-1] 
        for name in sorted_tasks:
            task = self.tasks[name]
            successors = [t for t in self.tasks.values() if name in t.predecessors]
            if not successors:
                task.lf = total_time
            else:
                task.lf = min(s.ls for s in successors)
            task.ls = task.lf - task.duration
            task.slack = task.lf - task.ef

        return total_time

    def get_critical_path(self):
        return [name for name, task in self.tasks.items() if task.slack == 0]

    def gantt_ascii(self):
        """
        Genera un cronograma Gantt en formato de texto ASCII.
        1 caracter = 5 días.
        """
        total_time = max(t.ef for t in self.tasks.values())
        scale = 5  # Cada caracter representa 5 días
        
        lines = []
        lines.append("  Cronograma del Proyecto (Diagrama de Gantt)")
        lines.append("  " + "═" * 70)
        
        # Cabecera de días (e.g. 0d, 30d, 60d...)
        header_days = ""
        for d in range(0, int(total_time) + 1, 30):
            header_days += f"{d}d".ljust(6)
        lines.append(f"  {'Actividad':<24} | {header_days}")
        lines.append("  " + "─" * 70)
        
        for name, task in self.tasks.items():
            start_chars = int(task.es / scale)
            duration_chars = max(1, int(task.duration / scale))
            slack_chars = int(task.slack / scale)
            
            bar = " " * start_chars
            bar += "█" * duration_chars
            if slack_chars > 0:
                bar += "░" * slack_chars
                
            crit_tag = " [CRIT]" if task.slack == 0 else ""
            lines.append(f"  {task.name + crit_tag:<24} | {bar}")
            
        lines.append("  " + "═" * 70)
        lines.append("  Leyenda: █ Trabajo Activo  ░ Holgura Total (Slack)")
        return "\n".join(lines)


def get_setp_phase2_planning():
    pm = PERTManager()
    # Tareas reales para la Fase 2 del SETP
    pm.add_task("Diseño", 30)
    pm.add_task("Licencias", 20, ["Diseño"])
    pm.add_task("Adquisición Predios", 60, ["Diseño"])
    pm.add_task("Obra Intercambiador N07", 120, ["Licencias", "Adquisición Predios"])
    pm.add_task("Señalización", 15, ["Obra Intercambiador N07"])
    pm.add_task("Capacitación Conductores", 30, ["Obra Intercambiador N07"])
    pm.add_task("Inauguración", 5, ["Señalización", "Capacitación Conductores"])
    
    total = pm.calculate()
    cp = pm.get_critical_path()
    return total, cp, pm.tasks
