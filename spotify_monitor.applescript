property lastArtUrl : ""

on idle
	tell application "Spotify"
		if application "Spotify" is running then
			set currentArtUrl to artwork url of current track
			set currentTrackTitle to name of current track
			set currentTrackArtist to artist of current track
			if currentArtUrl is not lastArtUrl then
				set lastArtUrl to currentArtUrl
				-- Path to the file in the Pictures directory subfolder
				set subfolderPath to (path to pictures folder as text) & "spotipapers:"
				-- Ensure the subfolder exists
				tell application "System Events"
					if not (exists folder subfolderPath) then
						make new folder at (path to pictures folder) with properties {name:"spotipapers"}
					end if
				end tell
				set outputFile to subfolderPath & "current_spotify_track_info.txt"
				set outputData to "Track Title: " & currentTrackTitle & linefeed & "Track Artist: " & currentTrackArtist & linefeed & "Artwork URL: " & currentArtUrl
				my write_to_file(outputData, outputFile)
			end if
		end if
	end tell
	return 5 -- Idle interval in seconds
end idle

-- Handler to write the data to a file
on write_to_file(this_data, target_file)
	try
		set target_file to target_file as text
		set open_file to open for access file target_file with write permission
		set eof of open_file to 0
		write this_data to open_file starting at eof
		close access open_file
	on error errMsg number errNum
		try
			close access file target_file
		end try
		display dialog "Error writing to file: " & errMsg
	end try
end write_to_file
