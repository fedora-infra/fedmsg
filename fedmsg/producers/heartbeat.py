from datetime import timedelta
from moksha.api.hub.producer import PollingProducer

import fedmsg.json


class HeartbeatProducer(PollingProducer):
    frequency = timedelta(seconds=2)

    def poll(self):
        # FIXME -- this should use fedmsg.send_message
        self.send_message(
            topic="org.fedoraproject._heartbeat",
            message=fedmsg.json.dumps({'msg': "lub-dub"})
        )
