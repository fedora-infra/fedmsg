import fedmsg.crypto
import moksha.api.hub.consumer


class FedmsgConsumer(moksha.api.hub.consumer.Consumer):
    validate_signatures = False

    def __init__(self, *args, **kwargs):
        super(FedmsgConsumer, self).__init__(*args, **kwargs)
        self.validate_signatures = self.hub.config.get('validate_signatures')

    def validate(self, message):
        """ This needs to raise an exception, caught by moksha. """

        # If we're not validating, then everything is valid.
        # If this is turned on globally, our child class can override it.
        if not self.validate_signatures:
            return

        if not fedmsg.crypto.validate(message['body'], **self.hub.config):
            raise RuntimeWarning("Failed to authn message.")
