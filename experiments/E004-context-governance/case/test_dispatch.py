import unittest

from dispatch import Event, active_movements, export


class DispatchTests(unittest.TestCase):
    def test_full_delivery_excludes_audit_notes_and_sorts(self):
        inbound = [
            Event(18, "ship", "P8", "west"),
            Event(5, "note", "P5"),
            Event(12, "ship", "P7", "east"),
        ]
        self.assertEqual([event.seq for event in export(iter(inbound))], [12, 18])

    def test_receiver_applies_revocations(self):
        inbound = [Event(2, "ship", "P7", "east"), Event(4, "void", "P7")]
        self.assertEqual(active_movements("east", export(inbound)), set())
