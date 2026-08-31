"""
Entry point do pacote de bots.
"""
from bots.bot_01_desktop_collector.collector import DesktopCollectorBot
from bots.bot_02_web_collector.collector import WebCollectorBot
from bots.bot_03_consolidator.consolidator import ConsolidatorBot
from bots.bot_04_ml_classifier.classifier import MLClassifierBot
from bots.bot_05_notifier_reporter.reporter import NotifierReporterBot

__all__ = [
    "DesktopCollectorBot",
    "WebCollectorBot",
    "ConsolidatorBot",
    "MLClassifierBot",
    "NotifierReporterBot",
]
