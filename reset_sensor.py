# Code to trigger reset

from modules.nexysio import Nexysio

# This is the driver code to do this 

nexys = Nexysio()
handle = nexys.autoopen()

nexys.spi_enable()
nexys.spi_reset()
nexys.spi_clkdiv = 255
nexys.send_routing_cmd()


nexys.testReset()

# This may or may not work, or it could cause issues. I will comment it out if needed.
nexys.close()