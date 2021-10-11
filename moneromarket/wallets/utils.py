def MergeIncomingAndOutgoing(incoming, outgoing):

	# Set up variables
	merged_list = [ ]  

	incoming_index = 0  
	outgoing_index = 0  

	incoming_length = len(incoming)  
	outgoing_length = len(outgoing)  


	# Go through each list
	while len(merged_list) < incoming_length + outgoing_length:

		if incoming_index == incoming_length:
			while outgoing_index != len(outgoing):
				merged_list.append((outgoing[outgoing_index], "outgoing"))  

				outgoing_index += 1  

			break  


		elif outgoing_index == outgoing_length:
			while incoming_index != len(incoming):
				merged_list.append((incoming[incoming_index], "incoming"))  

				incoming_index += 1  

			break  



		# Compare transaction heights
		if incoming[incoming_index].transaction.height > outgoing[outgoing_index].transaction.height:
			merged_list.append((incoming[incoming_index], "incoming"))  

			incoming_index += 1  

		else:
			merged_list.append((outgoing[outgoing_index], "outgoing"))  

			outgoing_index += 1  




	# It is a list of tuples to keep track of whether it is in incoming or ougoing transaction.
	# Transaction data is [0] and incoming/outgoing status is [1]
	return merged_list  